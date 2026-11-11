#!/usr/bin/env python3
"""Source-faithful FNS 1-YUR regional legal-entity statistics, from official ZIP/XLS.

The source publication is a monthly snapshot, not an SME-register observation.
Only reported indicators 1, 8 and 12 are retained. No counts are derived.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
import hashlib
from html.parser import HTMLParser
import io
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import zipfile

CORPUS = Path("scrolls/russia/authorities/federal-tax-service/legal-entity-registration")
PAGES = {
    2026: "16601803", 2025: "15764462", 2024: "14414858",
    2023: "13134463", 2022: "11892431", 2021: "10553558",
    2020: "9558929", 2019: "8376083", 2018: "7243238",
    2017: "6427754", 2016: "5953348", 2015: "5404042",
    2014: "4558837", 2013: "4161934", 2012: "4171842",
}
BASE = "https://www.nalog.gov.ru/rn77/related_activities/statistics_and_analytics/forms/"
INDICATORS = ((1, "c01"), (8, "c08"), (12, "c12"))
# The 2026 sample establishes a reviewed schema; older/changed releases fail closed.
KINDS_2026 = (
    "1000 1100 1110 1120 1130 1131 1140 1141 1142 1143 1144 "
    "1150 1151 1160 1170 1171 1172 1173 1174 1175 1176 1180 1190 "
    "1200 1210 1220 1221 1222 1230 1231 1232 1233 1240 1241 1242 "
    "1250 1251"
).split()
REGION_RE = re.compile(r"[0-9]{2}\Z")
DATE_RE = re.compile(r"(?<!\d)(0[1-9]|[12]\d|3[01])[./](0[1-9]|1[0-2])[./](20\d{2})(?!\d)")
OLE = bytes.fromhex("D0CF11E0A1B11AE1")
MAX_HTML, MAX_ZIP, MAX_XLS = 4_000_000, 30_000_000, 16_000_000


class SourceError(Exception):
    """Publisher, archive, schema, or evidence inconsistency."""


def check(value, reason):
    if not value:
        raise SourceError(reason)


def page_url(year):
    check(year in PAGES, "YEAR_PAGE_NOT_REVIEWED")
    return BASE + PAGES[year] + "/"


def file_for(d, root=CORPUS):
    return Path(root) / str(d.year) / (d.isoformat() + "_1-YUR.csv")


def allowed_url(url, kind):
    p = urlsplit(url)
    check(p.scheme == "https" and p.hostname in ("www.nalog.gov.ru", "www.nalog.ru")
          and p.port in (None, 443) and not p.username and not p.password
          and not p.fragment, "SOURCE_HOST_INVALID")
    if kind == "page":
        check(p.path.startswith("/rn") and "/related_activities/statistics_and_analytics/forms/" in p.path
              and p.path.endswith("/"), "SOURCE_PAGE_PATH_INVALID")
    else:
        source_path = p.path.replace("\\", "/")
        check(source_path.lower().endswith((".zip", ".rar", ".xls"))
              and ("/related_activities/statistics_and_analytics/forms/reg/" in source_path
                   or "/docs/otchet/" in source_path
                   or "/files/docs/gosreg/" in source_path), "SOURCE_ASSET_PATH_INVALID")
    return url


class OfficialRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        allowed_url(newurl, "zip" if req.full_url.lower().endswith(".zip") else "page")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(url, kind, limit):
    allowed_url(url, kind)
    opener = build_opener(OfficialRedirect())
    for attempt in range(3):
        try:
            with opener.open(Request(url, headers={"User-Agent": "Tabularium-FNS-1YUR/1.0",
                                                   "Accept-Encoding": "identity"}), timeout=30) as resp:
                allowed_url(resp.geturl(), kind)
                check(resp.status == 200, "SOURCE_HTTP_STATUS")
                check(resp.headers.get("Content-Encoding", "identity").lower() == "identity",
                      "SOURCE_ENCODING_UNEXPECTED")
                length = resp.headers.get("Content-Length")
                check(length is None or (length.isdecimal() and int(length) <= limit),
                      "SOURCE_TOO_LARGE")
                body = resp.read(limit + 1)
                check(0 < len(body) <= limit, "SOURCE_EMPTY_OR_TOO_LARGE")
                check(length is None or len(body) == int(length), "SOURCE_TRUNCATED")
                if kind == "zip":
                    check(body.startswith(b"PK\x03\x04"), "SOURCE_NOT_ZIP")
                else:
                    check(b"<html" in body[:2000].lower() or b"<!doctype html" in body[:2000].lower(),
                          "SOURCE_NOT_HTML")
                return body
        except HTTPError as exc:
            if attempt == 2 or exc.code not in (429, 500, 502, 503, 504):
                raise SourceError("HTTP_" + str(exc.code)) from None
        except (URLError, TimeoutError, OSError):
            if attempt == 2:
                raise SourceError("DOWNLOAD_FAILED") from None
        time.sleep(attempt + 1)
    raise SourceError("DOWNLOAD_FAILED")


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.entries = []
        self.href = None
        self.words = []
        self.recent = ''
        self.context = ''

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self.href = dict(attrs).get("href", "")
            self.context = self.recent[-240:]
            self.words = []

    def handle_data(self, data):
        self.recent = (self.recent + data)[-500:]
        if self.href is not None:
            self.words.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.href is not None:
            self.entries.append((self.href, self.context + " " + "".join(self.words)))
            self.href = None


def extract_releases(html, page):
    parser = AnchorParser()
    parser.feed(html.decode("utf-8-sig"))
    found = {}
    for href, label in parser.entries:
        url = urljoin(page, href.strip())
        try:
            allowed_url(url, "source")
        except SourceError:
            continue
        dates = DATE_RE.findall(label)
        if not dates:
            continue
        # The FNS link can say only 'Details'; the date precedes the anchor.
        day, month, year = map(int, dates[-1])
        try:
            d = date(year, month, day)
        except ValueError:
            raise SourceError("SOURCE_DATE_INVALID") from None
        check(day == 1, "SOURCE_REFERENCE_DAY_UNEXPECTED")
        if d in found and found[d] != url:
            raise SourceError("DUPLICATE_REFERENCE_DATE_LINK")
        found[d] = url
    check(found, "SOURCE_RELEASE_LINKS_MISSING")
    return found


def discover_year_pages(html):
    """Find explicitly linked future report pages in FNS's official forms index."""
    parser = AnchorParser()
    parser.feed(html.decode("utf-8-sig"))
    result = {}
    for href, label in parser.entries:
        match = re.findall(r"1\s*[-–]\s*ЮР\W+(20\d{2})\s*год", label,
                           flags=re.IGNORECASE)
        if not match:
            continue
        year = int(match[-1])
        url = urljoin(BASE, href)
        try:
            allowed_url(url, "page")
        except SourceError:
            continue
        check(url != BASE, "YEAR_INDEX_LINK_NOT_REPORT")
        if year in result and result[year] != url:
            raise SourceError("YEAR_PAGE_AMBIGUOUS")
        result[year] = url
    return result


def discover(years=None):
    years = years or (date.today().year, date.today().year - 1)
    wanted = sorted(set(years), reverse=True)
    unknown = [year for year in wanted if year not in PAGES]
    discovered = {}
    if unknown:
        discovered = discover_year_pages(download(BASE, "page", MAX_HTML))
    releases = {}
    for year in wanted:
        if year in PAGES:
            page = page_url(year)
        elif year in discovered:
            page = discovered[year]
        elif year >= 2027 and year == date.today().year:
            # The next-year page may not yet exist; its January issue can
            # still occur on the preceding year's official report page.
            print("FNS_1YUR_YEAR_PAGE_NOT_YET_PUBLISHED", year, file=sys.stderr)
            continue
        else:
            raise SourceError("YEAR_PAGE_UNAVAILABLE")
        for d, url in extract_releases(download(page, "page", MAX_HTML), page).items():
            if d in releases and releases[d][1] != url:
                if year == d.year:
                    releases[d] = (page, url)
                elif d.year != year + 1:
                    raise SourceError("CROSS_PAGE_DATE_AMBIGUOUS")
            else:
                releases[d] = (page, url)
    check(releases, "SOURCE_RELEASES_MISSING")
    return dict(sorted(releases.items()))


def display_name(name):
    """Decode legacy ZIP names for matching only; retain exact member name."""
    variants = [name]
    try:
        raw = name.encode("cp437")
        variants.extend([raw.decode("cp866"), raw.decode("cp1251")])
    except (UnicodeError, LookupError):
        pass
    return variants


def member_matches(name, d):
    for variant in display_name(name):
        simple = re.sub(r"\s+", " ", variant).lower()
        if (re.search(r"\(1\)\.xls\Z", simple)
                and not simple.startswith(("/", "\\")) and ".." not in simple.split("/")):
            dates = re.findall(r"(20\d{2})[_-](\d{2})[_-](\d{2})", simple)
            if dates and any(tuple(map(int, a)) != (d.year, d.month, d.day) for a in dates):
                raise SourceError("ARCHIVE_MEMBER_DATE_CONFLICT")
            return True
    return False


def choose_member(blob, d):
    check(blob.startswith(b"PK\x03\x04"), "SOURCE_NOT_ZIP")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        entries = z.infolist()
        check(0 < len(entries) <= 100, "ARCHIVE_MEMBER_COUNT_INVALID")
        check(sum(x.file_size for x in entries) <= 100_000_000, "ARCHIVE_TOTAL_SIZE_EXCEEDED")
        candidates = [x for x in entries if not x.is_dir() and member_matches(x.filename, d)]
        check(len(candidates) == 1, "ARCHIVE_MEMBER_MISSING_OR_AMBIGUOUS")
        item = candidates[0]
        check(0 < item.file_size <= MAX_XLS, "XLS_SIZE_INVALID")
        check(item.compress_size <= MAX_ZIP, "ARCHIVE_COMPRESSED_SIZE_INVALID")
        with z.open(item) as fp:
            xls = fp.read(MAX_XLS + 1)
        check(len(xls) == item.file_size and xls.startswith(OLE), "XLS_NOT_OLE")
        return xls, item.filename


def integer(value, what):
    if isinstance(value, bool):
        raise SourceError(what)
    if isinstance(value, (int, float)):
        check(0 <= value <= 10**12 and value == int(value), what)
        return str(int(value))
    if isinstance(value, str) and re.fullmatch(r"\d+", value):
        return str(int(value))
    raise SourceError(what)


def code(value, n):
    try:
        result = integer(value, "CODE_INVALID")
    except SourceError:
        return None
    return result.zfill(n) if len(result) <= n else None


def extract_xls(xls, d):
    check(xls.startswith(OLE) and len(xls) <= MAX_XLS, "XLS_SIGNATURE_INVALID")
    try:
        import xlrd
    except ImportError as exc:
        raise SourceError("XLRD_REQUIRED: pip install -r scripts/requirements_fns_1yur.txt") from exc
    try:
        book = xlrd.open_workbook(file_contents=xls, on_demand=True)
    except Exception as exc:
        raise SourceError("XLS_UNREADABLE") from exc
    try:
        kinds = sorted(n for n in book.sheet_names() if re.fullmatch(r"\d{4}", n) and n != "1300")
        check("1000" in kinds and "1100" in kinds and "1200" in kinds
              and len(kinds) >= 20 and set(kinds).issubset(set(KINDS_2026)),
              "KIND_CLASSIFICATION_REVIEW_REQUIRED")
        check("1300" in book.sheet_names(), "REFERENCE_SHEET_MISSING")
        result, national, special = {}, {}, {}
        for kind in kinds:
            sh = book.sheet_by_name(kind)
            check(sh.nrows >= 20 and sh.ncols >= 14, "KIND_SHEET_TRUNCATED")
            loc = {}
            for indicator, prefix in INDICATORS:
                matches = [c for c in range(sh.ncols)
                           if code(sh.cell_value(9, c), 2) == str(indicator).zfill(2)]
                check(len(matches) == 1, "INDICATOR_HEADER_AMBIGUOUS")
                loc[prefix] = matches[0]
            check(loc == {"c01": 2, "c08": 9, "c12": 13}, "INDICATOR_COLUMNS_CHANGED")
            national[kind] = {p: integer(sh.cell_value(10, c), "NATIONAL_COUNT_INVALID")
                              for p, c in loc.items()}
            for row in range(11, sh.nrows):
                key = code(sh.cell_value(row, 0), 2)
                if key is None or not REGION_RE.fullmatch(key):
                    continue
                name = sh.cell_value(row, 1)
                check(isinstance(name, str) and name.strip(), "REGION_NAME_MISSING")
                observed = {p: integer(sh.cell_value(row, c), "REGIONAL_COUNT_INVALID")
                            for p, c in loc.items()}
                if key in ("96", "99"):
                    check(all(v == "0" for v in observed.values()),
                          "UNMAPPED_TERRITORY_NONZERO")
                    special.setdefault(key, name)
                    continue
                data = result.setdefault(key, {"name": name, "kinds": {}})
                check(data["name"] == name, "REGION_NAME_CONFLICT")
                check(kind not in data["kinds"], "DUPLICATE_REGION_KIND")
                data["kinds"][kind] = observed
        check(len(result) >= 60 and all(set(x["kinds"]) == set(kinds) for x in result.values()),
              "REGIONAL_SCOPE_INCOMPLETE")
        for kind in kinds:
            for _, prefix in INDICATORS:
                check(sum(int(x["kinds"][kind][prefix]) for x in result.values())
                      == int(national[kind][prefix]), "NATIONAL_RECONCILIATION_FAILED")
        # The same 3 indicators appear a second time on region-specific sheets.
        for region, item in result.items():
            check(region in book.sheet_names(), "REGION_CONTROL_SHEET_MISSING")
            sh = book.sheet_by_name(region)
            check(sh.nrows >= 20 and sh.ncols >= 14, "REGION_CONTROL_SHEET_TRUNCATED")
            loc = {}
            for indicator, prefix in INDICATORS:
                matches = [c for c in range(sh.ncols)
                           if code(sh.cell_value(8, c), 2) == str(indicator).zfill(2)]
                check(len(matches) == 1, "REGION_CONTROL_HEADER_INVALID")
                loc[prefix] = matches[0]
            check(loc == {"c01": 2, "c08": 9, "c12": 13}, "REGION_CONTROL_COLUMNS_CHANGED")
            observed = {}
            for row in range(9, sh.nrows):
                kind = code(sh.cell_value(row, 1), 4)
                if kind not in kinds:
                    continue
                check(kind not in observed, "DUPLICATE_CONTROL_KIND")
                observed[kind] = {
                    p: integer(sh.cell_value(row, col), "CONTROL_COUNT_INVALID")
                    for p, col in loc.items()
                }
            check(observed == item["kinds"], "CROSS_ORIENTATION_MISMATCH")
        return result, kinds
    finally:
        book.release_resources()


def csv_columns(kinds):
    return ["region_code", "region_name"] + [
        prefix + "_" + kind for _, prefix in INDICATORS for kind in sorted(kinds)
    ]


def write_csv(rows, kinds):
    out = io.StringIO(newline="")
    w = csv.writer(out, lineterminator="\n")
    w.writerow(csv_columns(kinds))
    for region in sorted(rows):
        item = rows[region]
        w.writerow([region, item["name"]] +
                   [item["kinds"][kind][prefix] for _, prefix in INDICATORS
                    for kind in sorted(kinds)])
    return out.getvalue().encode("utf-8")


def read_csv(data):
    try:
        reader = csv.DictReader(io.StringIO(data.decode("utf-8"), newline=""))
        fields = reader.fieldnames
        check(fields is not None and fields[:2] == ["region_code", "region_name"]
              and len(fields) >= 5 and len(fields) == len(set(fields)), "CSV_HEADER_INVALID")
        kinds = sorted(set(field.split("_", 1)[1] for field in fields[2:] if "_" in field))
        check(fields == csv_columns(kinds), "CSV_SCHEMA_INVALID")
        parsed = {}
        for row in reader:
            check(None not in row and all(k in row for k in fields), "CSV_ROW_MALFORMED")
            key = row["region_code"]
            check(key not in parsed and REGION_RE.fullmatch(key or "") and
                  isinstance(row["region_name"], str) and row["region_name"].strip(),
                  "CSV_REGION_INVALID")
            for field in fields[2:]:
                integer(row[field], "CSV_COUNT_INVALID")
            parsed[key] = tuple(row[f] for f in fields)
        check(len(parsed) >= 60, "CSV_REGION_COUNT_INVALID")
        return fields, parsed
    except UnicodeError as exc:
        raise SourceError("CSV_ENCODING_INVALID") from exc


def compare(previous, candidate):
    _, fresh = read_csv(candidate)
    if previous is None:
        return "NEW", len(fresh)
    old_fields, old = read_csv(previous)
    new_fields, _ = read_csv(candidate)
    # A reviewed historical reclassification must not be silently rewritten.
    check(old_fields == new_fields, "CSV_SCHEMA_CHANGED")
    changes = sum(old.get(k) != fresh.get(k) for k in old.keys() | fresh.keys())
    return ("UPDATED" if changes else "NO_CHANGE", changes)


def capture(d, url):
    archive = download(url, "zip", MAX_ZIP)
    member, member_name = choose_member(archive, d)
    rows, kinds = extract_xls(member, d)
    return write_csv(rows, kinds), {
        "archive_url": url, "archive_sha256": hashlib.sha256(archive).hexdigest(),
        "member_name": member_name, "member_sha256": hashlib.sha256(member).hexdigest(),
        "regions": len(rows), "legal_kinds": len(kinds)
    }


def cli(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("discover", "capture", "validate"))
    ap.add_argument("--date")
    ap.add_argument("--year", type=int)
    ap.add_argument("--xls")
    ap.add_argument("--output")
    args = ap.parse_args(argv)
    if args.mode == "validate":
        print("FNS 1-YUR source contract valid")
        return
    releases = {} if args.xls else discover([args.year] if args.year else None)
    if args.mode == "discover":
        for day, (_, url) in releases.items():
            print(day, url)
        return
    check(args.date, "DATE_REQUIRED")
    d = date.fromisoformat(args.date)
    if args.xls:
        data = Path(args.xls).read_bytes()
        rows, kinds = extract_xls(data, d)
        candidate = write_csv(rows, kinds)
        print("Local source:", len(rows), "regions;", len(kinds), "kinds")
    else:
        check(d in releases, "DATE_NOT_PUBLISHED")
        candidate, _ = capture(d, releases[d][1])
    if args.output:
        Path(args.output).write_bytes(candidate)
    else:
        sys.stdout.buffer.write(candidate)


if __name__ == "__main__":
    try:
        cli()
    except (SourceError, ValueError) as exc:
        print("FNS_1YUR_ERROR:", exc, file=sys.stderr)
        sys.exit(2)
