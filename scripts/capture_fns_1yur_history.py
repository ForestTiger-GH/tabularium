#!/usr/bin/env python3
"""Historical FNS 1-YUR source archive adapter; source-faithful from 2012.

Historical indicators are selected by documented published column captions,
NOT by assuming that the modern 1/8/12 numbering applied in older editions.
The exact source indicator number remains in each resulting cNN_XXXX column.
"""
from __future__ import annotations
import csv
from datetime import date
import hashlib
from html.parser import HTMLParser
import io
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener
from urllib.error import HTTPError, URLError
import time

import capture_fns_1yur as modern

MIN_DATE = date(2012, 1, 1)
YEAR_PAGES = {
    2012: "4171842", 2013: "4161934", 2014: "4558837", 2015: "5404042",
    2016: "5953348", 2017: "6427754", 2018: "7243238", 2019: "8376083",
    2020: "9558929", 2021: "10553558", 2022: "11892431", 2023: "13134463",
    2024: "14414858", 2025: "15764462", 2026: "16601803",
}
BASE = "https://www.nalog.gov.ru/rn77/related_activities/statistics_and_analytics/forms/"
PATHS = ("/files/docs/gosreg/", "/html/sites/www.new.nalog.ru/docs/otchet/",
         "/html/sites/www.new.nalog.ru/files/related_activities/statistics_and_analytics/forms/reg/")
DATE_RX = re.compile(r"(?<!\d)(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])\.(20\d{2})(?!\d)")
MAX_SOURCE = 30_000_000


class HistoryError(modern.SourceError):
    pass


def permitted(url, *, page=False):
    p = urlsplit(url)
    if (p.scheme != "https" or p.hostname not in ("www.nalog.gov.ru", "www.nalog.ru")
            or p.port not in (None, 443) or p.username or p.password or p.fragment or p.query):
        raise HistoryError("SOURCE_HOST_OR_URL_UNAPPROVED")
    path = p.path.replace("\\", "/")
    if page:
        if not (path.startswith("/rn77/related_activities/statistics_and_analytics/forms/")
                and path.endswith("/")):
            raise HistoryError("SOURCE_PAGE_PATH_UNAPPROVED")
    elif not (any(path.startswith(prefix) for prefix in PATHS)
              and path.lower().endswith((".xls", ".rar", ".zip"))):
        raise HistoryError("SOURCE_ASSET_PATH_UNAPPROVED")
    return url


class CheckedRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        permitted(newurl, page=not req.full_url.lower().endswith((".rar", ".zip", ".xls")))
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def retrieve(url, *, page=False):
    permitted(url, page=page)
    limit = 4_000_000 if page else MAX_SOURCE
    opener = build_opener(CheckedRedirect())
    request = Request(url, headers={"User-Agent": "Tabularium-FNS-1YUR-2012-History",
                                    "Accept-Encoding": "identity"})
    for attempt in range(3):
        try:
            with opener.open(request, timeout=40) as response:
                permitted(response.geturl(), page=page)
                if response.status != 200:
                    raise HistoryError("SOURCE_HTTP_NOT_200")
                if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                    raise HistoryError("SOURCE_COMPRESSION_UNEXPECTED")
                size = response.headers.get("Content-Length")
                if size and (not size.isdecimal() or int(size) > limit):
                    raise HistoryError("SOURCE_TOO_LARGE")
                raw = response.read(limit + 1)
                if not 0 < len(raw) <= limit:
                    raise HistoryError("SOURCE_EMPTY_OR_TOO_LARGE")
                if size and len(raw) != int(size):
                    raise HistoryError("SOURCE_TRUNCATED")
                if page:
                    if b"<html" not in raw[:3000].lower() and b"<!doctype" not in raw[:3000].lower():
                        raise HistoryError("SOURCE_NOT_HTML")
                else:
                    ext = urlsplit(url).path.lower().rsplit(".", 1)[-1]
                    signatures = {"xls": modern.OLE, "rar": b"Rar!", "zip": bytes.fromhex("504b0304")}
                    if not raw.startswith(signatures[ext]):
                        raise HistoryError("SOURCE_MAGIC_MISMATCH")
                return raw
        except HTTPError as exc:
            if attempt == 2 or exc.code not in (429, 500, 502, 503, 504):
                raise HistoryError("SOURCE_HTTP_" + str(exc.code)) from None
        except (URLError, OSError, TimeoutError):
            if attempt == 2:
                raise HistoryError("SOURCE_NETWORK_FAILED") from None
        time.sleep(attempt + 1)
    raise HistoryError("SOURCE_NETWORK_FAILED")


class ListParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth, self.description, self.links = 0, [], []
        self.href = None
        self.items = []

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            if not self.depth:
                self.description, self.links = [], []
            self.depth += 1
        if tag == "a" and self.depth:
            self.href = dict(attrs).get("href", "")
            
    def handle_data(self, data):
        if self.depth:
            self.description.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.links.append(self.href.strip())
            self.href = None
        if tag == "li" and self.depth:
            self.depth -= 1
            if not self.depth:
                self.items.append((" ".join(self.description), self.links[:]))


def releases_from_page(raw, page):
    parser = ListParser()
    parser.feed(raw.decode("utf-8-sig"))
    result = {}
    for label, links in parser.items:
        matches = DATE_RX.findall(label)
        if (len(matches) != 1 or
                "регистрации юридических лиц" not in label.lower()):
            continue
        try:
            day = date(*map(int, reversed(matches[0])))
        except ValueError:
            raise HistoryError("SOURCE_DATE_BAD") from None
        if day < MIN_DATE or day.day != 1:
            continue
        candidates = []
        for href in links:
            asset = urljoin(page, href)
            try:
                permitted(asset)
                candidates.append(asset)
            except HistoryError:
                continue
        if not candidates:
            # Some historical month entries have no downloadable official XLS/RAR/ZIP.
            # Record the gap, but keep the independently verified other releases.
            print("::warning::FNS_HISTORY_OFFICIAL_FILE_UNAVAILABLE",
                  day.isoformat(), page, flush=True)
            continue
        if len(set(candidates)) != 1:
            raise HistoryError("SOURCE_ASSET_AMBIGUOUS:" + day.isoformat())
        if day in result and result[day] != candidates[0]:
            raise HistoryError("SOURCE_DATE_DUPLICATE")
        result[day] = candidates[0]
    if not result:
        raise HistoryError("YEAR_RELEASES_NOT_FOUND")
    return result


def discover(start=MIN_DATE, end=date(2026, 11, 1)):
    if not MIN_DATE <= start <= end <= date.today():
        raise HistoryError("HISTORY_RANGE_INVALID")
    gathered, errors = {}, []
    for year in range(start.year, min(end.year, 2026) + 1):
        page = BASE + YEAR_PAGES[year] + "/"
        try:
            releases = releases_from_page(retrieve(page, page=True), page)
            print("FNS_HISTORY_DISCOVERED_YEAR", year, len(releases), flush=True)
        except HistoryError as exc:
            errors.append((year, str(exc)))
            continue
        for day, asset in releases.items():
            if start <= day <= end:
                gathered.setdefault(day, []).append((year, page, asset))
    if errors:
        print("::warning::FNS_HISTORY_YEAR_DISCOVERY_ERRORS", errors, flush=True)
    selected = {}
    for day, variants in gathered.items():
        # The same issue sometimes appears on two yearly publication pages.
        variants.sort(key=lambda x: (x[0] != day.year, x[0] != day.year - 1))
        winner = variants[0]
        if sum(x[0] == winner[0] and x[2] != winner[2] for x in variants):
            raise HistoryError("SAME_YEAR_SOURCE_COLLISION")
        selected[day] = winner[1:]
    if not selected:
        raise HistoryError("HISTORY_RELEASES_ABSENT")
    return dict(sorted(selected.items())), errors


def member_name(names):
    valid = [name for name in names if name.lower().endswith(".xls") and len(name) < 300
             and not name.startswith(("/", "\\")) and ".." not in name.replace("\\", "/").split("/")]
    for pattern in (r"\(1\)\.xls\Z", r"_I\.xls\Z"):
        selected = [name for name in valid if re.search(pattern, name, flags=re.I)]
        if selected:
            if len(selected) != 1:
                raise HistoryError("MULTIPLE_PART_I_WORKBOOKS")
            return selected[0]
    if len(valid) == 1:
        return valid[0]
    raise HistoryError("PART_I_WORKBOOK_UNRESOLVED")


def workbook_from_asset(raw, asset):
    suffix = urlsplit(asset).path.lower().rsplit(".", 1)[-1]
    if suffix == "xls":
        data, member = raw, urlsplit(asset).path.rsplit("/", 1)[-1]
    elif suffix == "zip":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            members = z.infolist()
            if len(members) > 100 or sum(x.file_size for x in members) > 100_000_000:
                raise HistoryError("ZIP_ENTRIES_UNSAFE")
            member = member_name([x.filename for x in members if not x.is_dir()])
            info = z.getinfo(member)
            if info.file_size > modern.MAX_XLS:
                raise HistoryError("ZIP_MEMBER_TOO_LARGE")
            data = z.read(member)
    elif suffix == "rar":
        with tempfile.TemporaryDirectory(prefix="fns-1yur-") as tmp:
            path = Path(tmp) / "source.rar"
            path.write_bytes(raw)
            try:
                listing = subprocess.run(["bsdtar", "-tf", str(path)],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise HistoryError("RAR_READER_FAILED") from exc
            if listing.returncode or len(listing.stdout.splitlines()) > 100:
                raise HistoryError("RAR_LIST_FAILED")
            member = member_name(listing.stdout.splitlines())
            extracted = subprocess.run(["bsdtar", "-xOf", str(path), member],
                                       capture_output=True, timeout=45)
            if extracted.returncode:
                raise HistoryError("RAR_EXTRACT_FAILED")
            data = extracted.stdout
    else:
        raise HistoryError("SOURCE_FORMAT_UNSUPPORTED")
    if not 0 < len(data) <= modern.MAX_XLS or not data.startswith(modern.OLE):
        raise HistoryError("XLS_MEMBER_INVALID")
    return data, member, suffix


def _header_row(sheet):
    """Require both printed alphabetic column labels and source indicator 1."""
    matches = [
        row for row in range(min(22, sheet.nrows))
        if str(sheet.cell_value(row, 0)).strip().upper() in ("А", "A")
        and str(sheet.cell_value(row, 1)).strip().upper() in ("Б", "B")
        and modern.code(sheet.cell_value(row, 2), 2) == "01"
    ]
    if len(matches) != 1:
        raise HistoryError("INDICATOR_NUMBER_ROW_UNRESOLVED")
    return matches[0]


def indicator_plan(sheet):
    """Select constructs from the publisher's column captions and numbers.

    Older editions move or omit bankruptcy states. The raw source indicator
    number, not the present-day equivalent, becomes the CSV prefix.
    """
    header_row = _header_row(sheet)
    captions = {}
    for col in range(2, sheet.ncols):
        text = " ".join(str(sheet.cell_value(row, col)).replace("\n", " ").lower()
                        for row in range(4, header_row))
        captions[col] = re.sub(r"\s+", " ", text).strip()
    proceedings = [col for col, text in captions.items()
                   if re.search(r"процедур\w*.*банкротств", text)]
    ceased = [col for col, text in captions.items()
              if "в порядке банкротства" in text]
    if len(ceased) != 1 or len(proceedings) > 1:
        raise HistoryError("BANKRUPTCY_CAPTION_AMBIGUOUS")
    loc = {"total": 2, "ceased_bankruptcy": ceased[0]}
    if proceedings:
        loc["in_bankruptcy_procedure"] = proceedings[0]
    result = {}
    for meaning, col in loc.items():
        number = modern.code(sheet.cell_value(header_row, col), 2)
        if number is None:
            raise HistoryError("SOURCE_INDICATOR_CODE_MISSING")
        result[meaning] = (col, "c" + number, str(int(number)))
    if len({value[0] for value in result.values()}) != len(result):
        raise HistoryError("SOURCE_SELECTED_COLUMNS_OVERLAP")
    return header_row, result


def _geography(sheet, row):
    """Return the original geographic key without guessing a district code."""
    name = sheet.cell_value(row, 1)
    if not isinstance(name, str) or not name.strip():
        return None
    name_lower = name.strip().casefold()
    number = modern.code(sheet.cell_value(row, 0), 2)
    if name_lower == "российская федерация" or "федеральный округ" in name_lower:
        if number is not None:
            raise HistoryError("AGGREGATE_HAS_UNEXPECTED_NUMERIC_CODE")
        return ("", name)
    if number is not None and modern.REGION_RE.fullmatch(number):
        return (number, name)
    return None


def _kind_control(book, geography, kinds, mappings_by_kind, expected):
    """Cross-check each *reported* observation against its transposed sheet."""
    code, name = geography
    candidates = [code] if code else [name, name.strip()]
    sheet_name = next((n for n in candidates if n in book.sheet_names()), None)
    if sheet_name is None and not code:
        return 0
    if sheet_name is None:
        raise HistoryError("REGION_CONTROL_SHEET_MISSING:" + code)
    sheet = book.sheet_by_name(sheet_name)
    found = {}
    for row in range(sheet.nrows):
        if sheet.ncols < 3:
            continue
        kind = modern.code(sheet.cell_value(row, 1), 4)
        if kind not in kinds:
            continue
        if kind in found:
            raise HistoryError("DUPLICATE_CONTROL_KIND:" + str(geography))
        found[kind] = {}
        for meaning, (col, _, _) in mappings_by_kind[kind].items():
            if col >= sheet.ncols:
                raise HistoryError("CONTROL_MEASURE_COLUMN_MISSING")
            found[kind][meaning] = modern.integer(
                sheet.cell_value(row, col), "CONTROL_VALUE_NOT_INTEGER")
    if not found:
        if not code:
            return 0
        raise HistoryError("REGION_CONTROL_KIND_ABSENT:" + code)
    if set(found) != set(kinds) or found != expected:
        raise HistoryError("REGION_CONTROL_DISAGREES:" + str(geography))
    return sum(len(mappings_by_kind[kind]) for kind in kinds)


def extract_observations(xls, reference_date):
    """Preserve the complete printed geographic order and source metric coverage."""
    try:
        import xlrd
    except ImportError as exc:
        raise HistoryError("XLRD_REQUIRED") from exc
    try:
        book = xlrd.open_workbook(file_contents=xls, on_demand=True)
    except Exception as exc:
        raise HistoryError("XLS_UNREADABLE") from exc
    try:
        sheet_names = set(book.sheet_names())
        kinds = sorted(name for name in sheet_names
                       if re.fullmatch(r"1[0-2][0-9]{2}", name) and name != "1300")
        if not (15 <= len(kinds) <= 90 and "Российская Федерация" in sheet_names):
            raise HistoryError("LEGAL_KIND_SHEETS_UNEXPECTED")
        nation = book.sheet_by_name("Российская Федерация")
        summary_codes = {
            modern.code(nation.cell_value(r, 1), 4)
            for r in range(nation.nrows) if nation.ncols >= 2
        }
        if not set(kinds).issubset(summary_codes):
            raise HistoryError("SOURCE_NATIONAL_KIND_SUMMARY_INCOMPLETE")
        master_order = None
        records = {}
        common_mapping = None
        mappings_by_kind = {}
        for kind in kinds:
            sheet = book.sheet_by_name(kind)
            header_row = _header_row(sheet)
            if sheet.ncols == 3:
                # Publisher prints only indicator 1 for this legal-kind sheet.
                if modern.code(sheet.cell_value(header_row, 2), 2) != "01":
                    raise HistoryError("TOTAL_ONLY_SHEET_NUMBER_UNEXPECTED:" + kind)
                mapping = {"total": (2, "c01", "1")}
            else:
                if common_mapping is None:
                    header_row, mapping = indicator_plan(sheet)
                    common_mapping = dict(mapping)
                else:
                    mapping = common_mapping
                    for meaning, (col, _, number) in mapping.items():
                        if (sheet.ncols <= col or
                                modern.code(sheet.cell_value(header_row, col), 2)
                                != str(number).zfill(2)):
                            raise HistoryError(
                                "INDICATOR_CODE_DIFFERS_BETWEEN_KINDS:" +
                                kind + ":" + meaning)
            mappings_by_kind[kind] = mapping
            order = []
            for row in range(header_row + 1, sheet.nrows):
                geo = _geography(sheet, row)
                if geo is None:
                    continue
                counts = {
                    meaning: modern.integer(sheet.cell_value(row, col),
                                            "SOURCE_COUNT_NOT_INTEGER")
                    for meaning, (col, _, _) in mapping.items()
                }
                if geo in order:
                    raise HistoryError("DUPLICATE_GEOGRAPHY_ROW")
                order.append(geo)
                records.setdefault(geo, {})[kind] = counts
            if master_order is None:
                master_order = order
            elif order != master_order:
                raise HistoryError("SOURCE_GEOGRAPHIC_ROW_ORDER_CONFLICT:" + kind)
        if common_mapping is None:
            raise HistoryError("SOURCE_BANKRUPTCY_COLUMNS_NOT_PUBLISHED")
        if (not master_order or master_order[0][0] != "" or
                master_order[0][1].strip().casefold() != "российская федерация"):
            raise HistoryError("SOURCE_RUSSIA_ROW_NOT_FIRST")
        districts = [x for x in master_order if not x[0] and
                     "федеральный округ" in x[1].casefold()]
        subjects = [x for x in master_order if x[0]]
        if (not 6 <= len(districts) <= 9 or
                not 60 <= len(subjects) <= 110 or
                len(master_order) != 1 + len(districts) + len(subjects)):
            raise HistoryError("SOURCE_GEOGRAPHY_PERIMETER_UNEXPECTED")
        if len({code for code, _ in subjects}) != len(subjects):
            repeated = {
                code: [name for k, name in subjects if k == code]
                for code, _ in subjects
                if sum(1 for k, _ in subjects if k == code) > 1
            }
            raise HistoryError("SOURCE_TERRITORY_CODE_AMBIGUOUS:" +
                               repr(repeated))
        if any(set(records[geo]) != set(kinds) for geo in master_order):
            raise HistoryError("KIND_COVERAGE_INCOMPLETE")
        source_differences = []
        for kind in kinds:
            for meaning in mappings_by_kind[kind]:
                total = int(records[master_order[0]][kind][meaning])
                territorial = sum(int(records[geo][kind][meaning]) for geo in subjects)
                if total != territorial:
                    source_differences.append({
                        "kind_code": kind, "meaning": meaning,
                        "reported_russia": total, "sum_territorial_rows": territorial,
                        "difference": total - territorial,
                    })
        if source_differences:
            print("::warning::FNS_SOURCE_NATIONAL_TERRITORIAL_DIFFERENCES",
                  reference_date, len(source_differences),
                  source_differences[:5], flush=True)
        crosschecked = 0
        for geo in master_order:
            crosschecked += _kind_control(
                book, geo, kinds, mappings_by_kind, records[geo])
        result_columns = ["region_code", "region_name"]
        coverage = {}
        metric_order = ("total", "in_bankruptcy_procedure", "ceased_bankruptcy")
        for meaning in metric_order:
            matching = [kind for kind in kinds if meaning in mappings_by_kind[kind]]
            if not matching:
                continue
            prefixes = {mappings_by_kind[kind][meaning][1] for kind in matching}
            if len(prefixes) != 1:
                raise HistoryError("SOURCE_METRIC_CODE_INCONSISTENT")
            prefix = next(iter(prefixes))
            result_columns.extend(prefix + "_" + kind for kind in matching)
            coverage[meaning] = matching
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(result_columns)
        for geo in master_order:
            line = [geo[0], geo[1]]
            for meaning in metric_order:
                for kind in coverage.get(meaning, []):
                    line.append(records[geo][kind][meaning])
            writer.writerow(line)
        source_map = {
            meaning: {"source_column_index_0based": column,
                      "source_indicator": number, "csv_prefix": prefix}
            for meaning, (column, prefix, number) in common_mapping.items()
        }
        return output.getvalue().encode("utf-8"), {
            "rows": len(master_order),
            "regions": len(subjects),
            "federal_districts": len(districts),
            "legal_kinds": len(kinds),
            "source_indicator_map": source_map,
            "source_kind_metric_coverage": coverage,
            "crosschecked_values": crosschecked,
            "kind_codes": kinds,
            "national_territorial_differences": source_differences,
        }
    finally:
        book.release_resources()


def capture(reference_date, page, source_url):
    raw = retrieve(source_url)
    xls, member, format_name = workbook_from_asset(raw, source_url)
    data, shape = extract_observations(xls, reference_date)
    shape.update({"source_page": page, "archive_url": source_url,
                  "archive_sha256": hashlib.sha256(raw).hexdigest(),
                  "member_name": member, "member_sha256": hashlib.sha256(xls).hexdigest(),
                  "container_format": format_name})
    return data, shape
