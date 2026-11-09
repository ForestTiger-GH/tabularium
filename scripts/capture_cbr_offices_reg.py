#!/usr/bin/env python3
"""Capture CBR monthly territorial statistics as a source-traceable wide CSV.

No third-party packages. Fail closed on ambiguous XLSX layout; never infer values.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import urljoin, urlsplit, unquote
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
import xml.etree.ElementTree as ET
import zipfile

REPO = "ForestTiger-GH/tabularium"
CORPUS = "scrolls/russia/authorities/bank-of-russia/credit-institution-structural-units"
SOURCE_PAGE = "https://www.cbr.ru/statistics/bank_sector/lic/"
FILENAME = re.compile(r"DivisionsPerRegion_(\d{2})(\d{2})(\d{2})\.xlsx\Z", re.I)
CSV_NAME = re.compile(r"(20\d\d-\d\d-01)_OFFICES-REG\.csv\Z")
XML = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKGREL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
LIMIT_HTML = 5_000_000
LIMIT_XLSX = 8_000_000
LIMIT_UNPACKED = 30_000_000
LIMIT_CELLS = 80_000
MAX_WIDTH = 70
POLICY = ("AGENTS.md", "scripts/capture_cbr_offices_reg.py",
          ".github/workflows/capture-cbr-offices-reg.yml",
          "tests/test_capture_cbr_offices_reg.py", CORPUS + "/README.md")


class CaptureError(Exception):
    pass


def require(ok, reason):
    if not ok:
        raise CaptureError(reason)


def clean(value):
    result = re.sub(r"\s+", " ", value).strip()
    require("\ufffd" not in result and not any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in result),
            "INVALID_TEXT")
    return result


def output_name(d):
    require(d.day == 1 and d.year >= 2019, "INVALID_REPORT_DATE")
    return f"{d.isoformat()}_OFFICES-REG.csv"


def url_date(raw):
    u = urlsplit(raw)
    require(u.scheme == "https" and u.hostname in ("www.cbr.ru", "cbr.ru")
            and u.port in (None, 443) and not u.username and not u.password
            and not u.query and not u.fragment
            and u.path.startswith("/vfs/statistics/bank_system/"), "INVALID_SOURCE_URL")
    m = FILENAME.fullmatch(unquote(u.path.rsplit("/", 1)[-1]))
    require(m is not None, "INVALID_XLSX_NAME")
    try:
        d = date(2000 + int(m[3]), int(m[2]), int(m[1]))
    except ValueError:
        raise CaptureError("INVALID_REPORT_DATE") from None
    output_name(d)
    return d


class NoRedirectOutsideCBR(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        p = urlsplit(newurl)
        require(p.scheme == "https" and p.hostname in ("www.cbr.ru", "cbr.ru")
                and p.port in (None, 443) and not p.username and not p.password,
                "REDIRECT_OUTSIDE_CBR")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(url, max_bytes, mimes):
    opener = build_opener(NoRedirectOutsideCBR())
    for attempt in range(3):
        try:
            request = Request(url, headers={"User-Agent": "Tabularium-CBR-Offices-REG/1.0",
                                            "Accept-Encoding": "identity"})
            with opener.open(request, timeout=25) as res:
                require(res.status == 200, "SOURCE_HTTP_STATUS")
                require(urlsplit(res.geturl()).hostname in ("www.cbr.ru", "cbr.ru"),
                        "SOURCE_REDIRECT_INVALID")
                mime = res.headers.get_content_type().lower()
                require(mime in mimes, "SOURCE_MIME_INVALID")
                require(res.headers.get("Content-Encoding", "identity").lower() == "identity",
                        "SOURCE_COMPRESSION_UNEXPECTED")
                size = res.headers.get("Content-Length")
                require(size is None or (size.isdecimal() and int(size) <= max_bytes),
                        "SOURCE_CONTENT_LENGTH")
                blob = res.read(max_bytes + 1)
                require(blob and len(blob) <= max_bytes, "SOURCE_SIZE_INVALID")
                require(size is None or len(blob) == int(size), "SOURCE_INCOMPLETE")
                return blob
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            if attempt == 2 or isinstance(e, HTTPError) and e.code not in (429, 500, 502, 503, 504):
                raise CaptureError("DOWNLOAD_FAILED") from e
            time.sleep(2 * (attempt + 1))
    raise CaptureError("DOWNLOAD_FAILED")


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.href = None
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.text = []

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.links.append((self.href, clean(" ".join(self.text))))
            self.href = None


def discover(html):
    parser = PageLinks()
    parser.feed(html)
    parser.close()
    found = {}
    for href, label in parser.links:
        u = urljoin(SOURCE_PAGE, href)
        if not FILENAME.fullmatch(unquote(urlsplit(u).path.rsplit("/", 1)[-1])):
            continue
        d = url_date(u)
        # The official link caption must agree with the date in the target filename.
        lab = re.search(r"(20\d{2})\s*г\.?:\s*на\s*(\d{2})\.(\d{2})", label, re.I)
        require(lab is not None and (int(lab[1]), int(lab[2]), int(lab[3])) ==
                (d.year, d.day, d.month), "SOURCE_LINK_DATE_MISMATCH")
        require(d not in found or found[d] == u, "SOURCE_DUPLICATE_REPORT_DATE")
        found[d] = u
    require(len(found) >= 1, "SOURCE_INDEX_INCOMPLETE")
    return dict(sorted(found.items()))


def colnum(ref):
    letters = re.match(r"[A-Z]+", ref)
    require(letters is not None, "XLSX_CELL_REFERENCE")
    n = 0
    for ch in letters[0]:
        n = n * 26 + ord(ch) - 64
    require(1 <= n <= MAX_WIDTH, "XLSX_COLUMN_LIMIT")
    return n


def xlsx_rows(blob):
    require(len(blob) <= LIMIT_XLSX and blob[:2] == b"PK", "XLSX_NOT_ZIP")
    z = zipfile.ZipFile(io.BytesIO(blob))
    files = {item.filename: item for item in z.infolist()}
    require(len(files) <= 250 and sum(x.file_size for x in files.values()) <= LIMIT_UNPACKED,
            "XLSX_UNPACKED_LIMIT")
    require(not any(x.flag_bits & 1 or ".." in x.filename.split("/") or x.filename.startswith("/")
                    for x in files.values()), "XLSX_UNSAFE_ENTRIES")
    require("xl/workbook.xml" in files and "xl/_rels/workbook.xml.rels" in files,
            "XLSX_MISSING_WORKBOOK")
    shared = []
    if "xl/sharedStrings.xml" in files:
        ss = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for item in ss.findall(XML + "si"):
            shared.append("".join(n.text or "" for n in item.iter(XML + "t")))
    relations = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    relmap = {r.get("Id"): r.get("Target") for r in relations.findall(PKGREL + "Relationship")}
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    sheets = wb.find(XML + "sheets")
    require(sheets is not None, "XLSX_NO_SHEETS")
    out = []
    count = 0
    for sh in sheets.findall(XML + "sheet"):
        name = clean(sh.get("name") or "")
        require(name and "\n" not in name, "XLSX_BAD_SHEET_NAME")
        relation = relmap.get(sh.get(REL + "id"), "")
        require(relation and not relation.startswith(("http:", "https:")) and ".." not in relation.split("/"),
                "XLSX_BAD_SHEET_RELATION")
        target = relation.lstrip("/") if relation.startswith("/") else "xl/" + relation
        require(target in files, "XLSX_MISSING_SHEET")
        tree = ET.fromstring(z.read(target))
        sheetdata = tree.find(XML + "sheetData")
        if sheetdata is None:
            continue
        data = []
        formulas = {}
        for r in sheetdata.findall(XML + "row"):
            rid = int(r.get("r", "0"))
            require(1 <= rid <= 30000, "XLSX_ROW_LIMIT")
            cells = {}
            for c in r.findall(XML + "c"):
                count += 1
                require(count <= LIMIT_CELLS, "XLSX_CELL_LIMIT")
                ref = c.get("r", "")
                column = colnum(ref)
                kind = c.get("t", "n")
                v = c.find(XML + "v")
                formula = c.find(XML + "f")
                if formula is not None:
                    # Preserve the publisher's cached value, NEVER evaluate the formula.
                    require(v is not None and v.text is not None,
                            "XLSX_FORMULA_CACHE_MISSING")
                    formulas[(rid, column)] = {
                        "formula": formula.text or "",
                        "attributes": dict(sorted(formula.attrib.items())),
                    }
                if kind == "inlineStr":
                    x = c.find(XML + "is")
                    value = "" if x is None else "".join(t.text or "" for t in x.iter(XML + "t"))
                elif kind == "s":
                    require(v is not None and v.text is not None, "XLSX_BAD_STRING_ID")
                    index = int(v.text)
                    require(0 <= index < len(shared), "XLSX_BAD_STRING_ID")
                    value = shared[index]
                elif kind in ("n", "str", "d"):
                    value = "" if v is None or v.text is None else v.text
                elif kind == "b":
                    require(v is not None and v.text in ("0", "1"), "XLSX_BAD_BOOLEAN")
                    value = "TRUE" if v.text == "1" else "FALSE"
                elif kind == "e":
                    raise CaptureError("XLSX_SOURCE_ERROR_VALUE")
                else:
                    raise CaptureError("XLSX_UNSUPPORTED_TYPE")
                value = clean(value)
                require(column not in cells, "XLSX_DUPLICATE_CELL")
                if value:
                    cells[column] = value
            if cells:
                data.append((rid, cells))
        if data:
            out.append((name, data, formulas))
    require(len(out) == 1, "XLSX_EXPECTED_SINGLE_DATA_SHEET")
    return out[0]


def is_quantitative(value):
    return re.fullmatch(r"[+-]?\d+(?:[.,]\d+)?", value) is not None


def is_district_label(value):
    # The source's generic grouping label, not a hardcoded district name list.
    return "федеральный округ" in value.casefold()


def last_district_boundary(data, district_index, territory_col, indicator_cols):
    """Resolve the end of the last district without assigning trailing regions to it.

    The publication may append territories outside the preceding federal district.
    Reconcile the published district subtotal against its following rows. This
    only determines extraction grouping; it does not alter any published value.
    """
    district = data[district_index][1]
    following = data[district_index + 1:]
    require(following, "XLSX_FINAL_DISTRICT_EMPTY")
    comparable = [c for c in indicator_cols
                  if district.get(c, "").isascii() and district.get(c, "").isdecimal()
                  and all(cells.get(c, "").isascii() and cells.get(c, "").isdecimal()
                          for _, cells in following)]
    require(len(comparable) >= 2, "XLSX_FINAL_DISTRICT_BALANCE_UNKNOWN")
    targets = {c: int(district[c]) for c in comparable}
    totals = {c: 0 for c in comparable}
    matches = []
    for offset, (_, cells) in enumerate(following, start=1):
        for c in comparable:
            totals[c] += int(cells[c])
        if totals == targets:
            matches.append(district_index + offset)
    require(len(matches) == 1, "XLSX_FINAL_DISTRICT_BALANCE_AMBIGUOUS")
    return matches[0]


def convert_xlsx(blob, *, return_formula_lineage=False):
    """Keep only the published table and attach source-derived district context."""
    sheet, rows, formulas = xlsx_rows(blob)
    starts = [(i, k) for i, (_, cells) in enumerate(rows) for k, value in cells.items()
              if "российская федерация" in value.casefold()
              and sum(is_quantitative(v) for v in cells.values()) >= 2]
    require(len(starts) == 1, "XLSX_NATIONAL_TOTAL_AMBIGUOUS")
    idx, territory_col = starts[0]
    require("российская федерация" in rows[idx][1].get(territory_col, "").casefold(),
            "XLSX_NATIONAL_TOTAL_POSITION")

    previous = rows[max(0, idx - 6):idx]
    # The title is not a table heading. Numbered column guides (1, 2, 3...)
    # are not source indicator names, even when adjacent to the heading row.
    header_candidates = [cells for _, cells in previous
                         if any(k > territory_col for k in cells)
                         and not (len(cells) >= 3 and
                                  all(value.isdecimal() and int(value) == k
                                      for k, value in cells.items()))]
    require(header_candidates, "XLSX_HEADER_ABSENT")
    require(not any(rid in {r for r, _ in previous} for rid, _ in formulas),
            "XLSX_FORMULA_IN_HEADER")

    data = []
    footer_started = False
    for rid, cells in rows[idx:]:
        name = cells.get(territory_col, "")
        number_count = sum(is_quantitative(v) for k, v in cells.items()
                           if k > territory_col)
        if number_count >= 2:
            require(not footer_started, "XLSX_DATA_AFTER_FOOTER")
            require(name, "XLSX_UNLABELLED_DATA_ROW")
            data.append((rid, cells))
        else:
            require(not number_count, "XLSX_AMBIGUOUS_NON_DATA_ROW")
            footer_started = True
    require(len(data) >= 30 and len({r for r, _ in data}) == len(data),
            "XLSX_TOO_FEW_REGIONS")
    cols = sorted({k for _, cells in data for k in cells})
    require(territory_col in cols and len(cols) >= 4, "XLSX_FEW_INDICATORS")
    indicator_cols = [k for k in cols if k > territory_col]

    header = []
    for k in cols:
        parts = []
        for candidate in header_candidates:
            value = candidate.get(k)
            if value and (not parts or parts[-1] != value):
                parts.append(value)
        if not parts:
            parts = [f"source_column_{k}"]
        header.append(" / ".join(parts))
    require(len(set(header)) == len(header), "XLSX_DUPLICATE_HEADER")

    districts = [i for i, (_, cells) in enumerate(data)
                 if is_district_label(cells[territory_col])]
    final_boundary = (last_district_boundary(data, districts[-1], territory_col,
                                             indicator_cols) if districts else None)
    last_section = ""
    records = [["source_row", "section_label", *header]]
    formula_lineage = {}
    for i, (rid, cells) in enumerate(data):
        name = cells[territory_col]
        if i in districts:
            # The source's district subtotal row supplies a structural section
            # label; do not duplicate its aggregate numeric values in the CSV.
            last_section = name
            continue
        if final_boundary is not None and i > final_boundary:
            section = ""  # These territories have no published district heading.
        else:
            section = last_section
        source_formulas = {str(col): formula for (r, col), formula in formulas.items()
                           if r == rid}
        if source_formulas:
            formula_lineage[str(rid)] = source_formulas
        records.append([str(rid), section, *(cells.get(k, "") for k in cols)])
    result = serialize(records)
    return (result, formula_lineage) if return_formula_lineage else result


def serialize(records):
    stream = io.StringIO(newline="")
    csv.writer(stream, lineterminator="\n").writerows(records)
    return stream.getvalue().encode("utf-8")


def validate_csv(blob):
    require(blob and not blob.startswith(b"\xef\xbb\xbf") and len(blob) < 8_000_000,
            "CSV_BAD_SIZE")
    try:
        rows = list(csv.reader(io.StringIO(blob.decode("utf-8"), newline=""), strict=True))
    except (UnicodeError, csv.Error):
        raise CaptureError("CSV_READ_FAILED") from None
    require(len(rows) >= 31, "CSV_TOO_FEW_ROWS")
    width = len(rows[0])
    require(6 <= width <= MAX_WIDTH + 2 and rows[0][:2] == ["source_row", "section_label"]
            and all(rows[0][2:]) and len(set(rows[0])) == width, "CSV_HEADER_INVALID")
    previous = 0
    for row in rows[1:]:
        require(len(row) == width and row[0].isascii() and row[0].isdecimal(),
                "CSV_ROW_INVALID")
        require(1 <= int(row[0]) <= 30000 and int(row[0]) > previous, "CSV_ROW_ORDER")
        require(all(clean(value) == value for value in row), "CSV_CELL_NONCANONICAL")
        previous = int(row[0])
    require(serialize(rows) == blob, "CSV_NON_CANONICAL")
    return len(rows)-1


def collect(mode, start, end, output_dir):
    require(output_dir.is_dir() and not any(output_dir.iterdir()), "OUTPUT_NOT_EMPTY")
    page = download(SOURCE_PAGE, LIMIT_HTML, {"text/html", "application/xhtml+xml"})
    try:
        links = discover(page.decode("utf-8-sig"))
    except UnicodeDecodeError:
        raise CaptureError("PAGE_ENCODING_INVALID") from None
    if mode == "daily":
        existing = []
        root = Path(CORPUS)
        for csv_file in root.glob("20??/*_OFFICES-REG.csv"):
            match = CSV_NAME.fullmatch(csv_file.name)
            if match:
                existing.append(date.fromisoformat(match[1]))
        days = ([d for d in links if d > max(existing)] if existing else [max(links)])
    else:
        days = [d for d in links if (start is None or start <= d) and (end is None or d <= end)]
    manifest = []
    for d in days:
        already = Path(CORPUS) / str(d.year) / output_name(d)
        if already.exists():
            require(already.is_file() and not already.is_symlink(), "EXISTING_TARGET_INVALID")
            validate_csv(already.read_bytes())
            print(f"SKIPPED_EXISTING {already}")
            continue
        target = output_dir / output_name(d)
        raw = download(links[d], LIMIT_XLSX, {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/octet-stream", "application/zip"})
        data, formula_lineage = convert_xlsx(raw, return_formula_lineage=True)
        validate_csv(data)
        target.write_bytes(data)
        manifest.append({"file": target.name, "source_url": links[d],
                         "xlsx_sha256": hashlib.sha256(raw).hexdigest(),
                         "csv_sha256": hashlib.sha256(data).hexdigest(),
                         "formula_cells": formula_lineage})
    return manifest


def git(*args, check=True):
    x = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=45, check=False)
    if check and x.returncode:
        raise CaptureError("GIT_" + args[0].upper().replace("-", "_"))
    return x


def gitstr(*args):
    return git(*args).stdout.decode("utf-8").strip()


def publish(root, input_dir, manifest_path, code_sha):
    require(os.getenv("GITHUB_REPOSITORY") == REPO and os.getenv("GITHUB_REF") == "refs/heads/main"
            and os.getenv("GITHUB_EVENT_REPOSITORY_PRIVATE", "false") == "false",
            "GITHUB_CONTEXT_INVALID")
    require(re.fullmatch(r"[0-9a-f]{40}", code_sha or "") is not None,
            "CODE_SHA_INVALID")
    require(gitstr("rev-parse", "HEAD") == code_sha and
            gitstr("rev-parse", "--show-toplevel") == str(root.resolve()),
            "GIT_CHECKOUT_INVALID")
    require(not git("status", "--porcelain", "--untracked-files=all").stdout,
            "GIT_DIRTY_WORKTREE")
    metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(isinstance(metadata, list) and metadata, "MANIFEST_EMPTY")
    require(len({x["file"] for x in metadata}) == len(metadata), "MANIFEST_DUPLICATES")
    additions = {}
    for item in metadata:
        name = item["file"]
        require(CSV_NAME.fullmatch(name) is not None, "INVALID_CSV_FILENAME")
        require(item["source_url"] and url_date(item["source_url"]).isoformat() == name[:10],
                "MANIFEST_SOURCE_MISMATCH")
        data = (input_dir / name).read_bytes()
        validate_csv(data)
        require(hashlib.sha256(data).hexdigest() == item["csv_sha256"], "MANIFEST_HASH_MISMATCH")
        lineage = item.get("formula_cells")
        require(isinstance(lineage, dict), "MANIFEST_FORMULAS_INVALID")
        parsed = list(csv.reader(io.StringIO(data.decode("utf-8"), newline="")))
        included_rows = {row[0] for row in parsed[1:]}
        for source_row, columns in lineage.items():
            require(source_row in included_rows and isinstance(columns, dict) and columns,
                    "MANIFEST_FORMULAS_INVALID")
            for column, formula in columns.items():
                require(column.isdecimal() and 1 <= int(column) <= MAX_WIDTH
                        and isinstance(formula, dict) and isinstance(formula.get("formula"), str)
                        and isinstance(formula.get("attributes"), dict),
                        "MANIFEST_FORMULAS_INVALID")
        relative = f"{CORPUS}/{name[:4]}/{name}
        additions[relative] = (data, item)
    require(all(not (root / f).is_symlink() for f in additions), "TARGET_SYMLINK")
    for attempt in range(3):
        git("fetch", "--no-tags", "origin", "refs/heads/main")
        head = gitstr("rev-parse", "FETCH_HEAD")
        require(not git("merge-base", "--is-ancestor", code_sha, head, check=False).returncode,
                "POLICY_COMMIT_NOT_ANCESTOR")
        changed = git("diff", "--name-only", code_sha, head, "--", *POLICY).stdout
        require(not changed, "POLICY_CHANGED_DURING_RUN")
        missing = {}
        for f, (data, item) in additions.items():
            existing = git("show", f"{head}:{f}", check=False)
            if existing.returncode == 0:
                require(existing.stdout == data, "IMMUTABLE_CSV_CONFLICT")
            else:
                missing[f] = (data, item)
        if not missing:
            print("NOOP_ALL_ALREADY_PUBLISHED")
            return
        for f, (data, _) in missing.items():
            p = root / f
            p.parent.mkdir(parents=True, exist_ok=True)
            require(not p.exists() and not p.is_symlink(), "TARGET_ALREADY_EXISTS")
            p.write_bytes(data)
        git("read-tree", head)
        git("add", "--", *missing)
        staged = git("diff", "--cached", "--name-only", head).stdout.decode().splitlines()
        require(set(staged) == set(missing), "UNEXPECTED_STAGED_PATHS")
        git("config", "user.name", "github-actions[bot]")
        git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
        tree = gitstr("write-tree")
        details = "\n".join(
            f"{f} source={item['source_url']} xlsx_sha256={item['xlsx_sha256']}\n"
            f"formula_cells={json.dumps(item['formula_cells'], ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"
            for f, (_, item) in missing.items())
        message = f"data(cbr): archive {len(missing)} regional offices releases\n\n{details}"
        require(len(message.encode("utf-8")) <= 95000, "COMMIT_PROVENANCE_TOO_LARGE")
        commit = gitstr("commit-tree", tree, "-p", head, "-m", message)
        pushed = git("push", "origin", f"{commit}:refs/heads/main", check=False)
        if pushed.returncode == 0:
            print(f"PUBLISHED {len(missing)} files commit={commit}")
            return
        # Restore local worktree before retry, without ever touching existing corpus entries.
        for f in missing:
            (root / f).unlink()
    raise CaptureError("PUBLISH_RETRY_EXHAUSTED")


def day(s):
    if not s:
        return None
    d = date.fromisoformat(s)
    require(d.day == 1, "DATE_NOT_FIRST_OF_MONTH")
    return d


def main():
    p = argparse.ArgumentParser(description=__doc__)
    cmd = p.add_subparsers(dest="command", required=True)
    cap = cmd.add_parser("capture")
    cap.add_argument("--mode", choices=("daily", "backfill"), required=True)
    cap.add_argument("--from-date")
    cap.add_argument("--to-date")
    cap.add_argument("--output-dir", type=Path, required=True)
    cap.add_argument("--manifest", type=Path, required=True)
    pub = cmd.add_parser("publish")
    pub.add_argument("--input-dir", type=Path, required=True)
    pub.add_argument("--manifest", type=Path, required=True)
    pub.add_argument("--code-sha", required=True)
    val = cmd.add_parser("validate")
    val.add_argument("--file", type=Path, required=True)
    args = p.parse_args()
    try:
        if args.command == "capture":
            a, b = day(args.from_date), day(args.to_date)
            require(not (a and b) or a <= b, "INVALID_DATE_RANGE")
            manifest = collect(args.mode, a, b, args.output_dir)
            args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"CAPTURED {len(manifest)} CSV")
        elif args.command == "validate":
            print(f"VALID {validate_csv(args.file.read_bytes())} observations")
        elif args.command == "publish":
            publish(Path.cwd(), args.input_dir, args.manifest, args.code_sha)
    except (CaptureError, OSError, ValueError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
