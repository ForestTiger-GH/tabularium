#!/usr/bin/env python3
"""Source-faithful regional SME counts from the FNS published statistics JSON.

Python 3.12 standard library only. Never invent historical dates, regions or zeros.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

SOURCE_PAGE = "https://rmsp.nalog.ru/statistics.html"
SOURCE_JSON = "https://rmsp.nalog.ru/statistics-proc.json"
CORPUS = Path("scrolls/russia/authorities/federal-tax-service/sme-registry-statistics")
COLUMNS = ("region_code", "region_name", "total", "ul_micro", "ul_small",
           "ul_medium", "ip_micro", "ip_small", "ip_medium")
SOURCE_COLUMNS = ("ssrf", "name", "cnt_total", "cnt_ul_micro", "cnt_ul_mini",
                  "cnt_ul_normal", "cnt_ip_micro", "cnt_ip_mini", "cnt_ip_normal")
LIMIT_HTML = 3_000_000
LIMIT_JSON = 4_000_000
DATE_VALUE = re.compile(r"\d{2}\.\d{2}\.20\d{2}\Z")
NAME = re.compile(r"(20\d\d-\d\d-\d\d)_SME-REG\.csv\Z")


class FnsError(Exception):
    """Source, schema, or publication contract violation."""


def require(condition, code):
    if not condition:
        raise FnsError(code)


def parse_date(value):
    try:
        result = datetime.strptime(value, "%d.%m.%Y").date()
    except (TypeError, ValueError):
        raise FnsError("DATE_INVALID") from None
    require(result >= date(2016, 8, 1), "DATE_OUT_OF_RANGE")
    require(result <= datetime.now(timezone(timedelta(hours=3))).date(), "DATE_IN_FUTURE")
    return result


def iso_to_date(value):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise FnsError("ISO_DATE_INVALID") from None


def file_for(d, root=CORPUS):
    return Path(root) / str(d.year) / f"{d.isoformat()}_SME-REG.csv"


def format_source_date(d):
    return d.strftime("%d.%m.%Y")


class FnsOnlyRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def check_url(url):
    p = urlsplit(url)
    require(p.scheme == "https" and p.hostname == "rmsp.nalog.ru"
            and p.port in (None, 443) and not p.username and not p.password
            and not p.fragment and p.path in ("/statistics.html", "/statistics-proc.json")
            and not p.query, "URL_NOT_ALLOWED")


def get_official(url, *, data=None, max_size=LIMIT_JSON):
    check_url(url)
    opener = build_opener(FnsOnlyRedirect())
    accept = "text/html" if data is None else "application/json"
    request = Request(url, data=data, method="GET" if data is None else "POST",
                      headers={"User-Agent": "Tabularium-FNS-SME/1.0",
                               "Accept": accept, "Accept-Encoding": "identity",
                               "Content-Type": "application/x-www-form-urlencoded"})
    for attempt in range(3):
        try:
            with opener.open(request, timeout=25) as response:
                check_url(response.geturl())
                require(response.status == 200, "HTTP_NOT_200")
                mime = response.headers.get_content_type().lower()
                require(mime in (("text/html", "application/xhtml+xml") if data is None
                                 else ("application/json",)), "SOURCE_MIME_INVALID")
                require(response.headers.get("Content-Encoding", "identity").lower() == "identity",
                        "ENCODING_UNEXPECTED")
                length = response.headers.get("Content-Length")
                require(length is None or (length.isdigit() and int(length) <= max_size),
                        "SOURCE_TOO_LARGE")
                raw = response.read(max_size + 1)
                require(0 < len(raw) <= max_size, "SOURCE_SIZE_INVALID")
                require(length is None or len(raw) == int(length), "SOURCE_TRUNCATED")
                return raw
        except HTTPError as e:
            if attempt == 2 or e.code not in (429, 500, 502, 503, 504):
                raise FnsError(f"HTTP_{e.code}") from None
        except (URLError, OSError, TimeoutError):
            if attempt == 2:
                raise FnsError("DOWNLOAD_FAILED") from None
        time.sleep(1 + attempt)
    raise FnsError("DOWNLOAD_FAILED")


class DateOptions(HTMLParser):
    def __init__(self):
        super().__init__()
        self.dates = set()

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "option":
            return
        value = dict(attrs).get("value", "")
        if DATE_VALUE.fullmatch(value):
            self.dates.add(parse_date(value))


def discover_dates(*, html=None):
    if html is None:
        html = get_official(SOURCE_PAGE, max_size=LIMIT_HTML)
    try:
        page = html.decode("utf-8")
    except UnicodeDecodeError:
        raise FnsError("HTML_NOT_UTF8") from None
    parser = DateOptions()
    parser.feed(page)
    parser.close()
    dates = sorted(parser.dates)
    require(len(dates) >= 2, "SOURCE_DATES_UNAVAILABLE")
    require(dates[0] == date(2016, 8, 1), "SOURCE_DATES_START_UNEXPECTED")
    return dates


def counter(value):
    require(type(value) is int and value >= 0 or
            isinstance(value, str) and bool(re.fullmatch(r"(0|[1-9]\d*)", value)),
            "COUNT_NOT_NONNEGATIVE_INTEGER")
    # The JSON endpoint publishes some years as decimal strings, others as JSON integers.
    return str(value)


def published_date(value):
    require(isinstance(value, str) and re.fullmatch(r"\d\d\.\d\d\.20\d\d 00:00:00", value),
            "SOURCE_DATE_FORMAT_CHANGED")
    return parse_date(value[:10])


def decode_snapshot(blob, d):
    try:
        decoded = json.loads(blob.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise FnsError("JSON_INVALID") from None
    require(isinstance(decoded, list) and 80 <= len(decoded) <= 200,
            "SOURCE_ROWS_INVALID")
    rows = {}
    levels = {0: 0, 1: 0, 2: 0}
    national = None
    for item in decoded:
        require(isinstance(item, dict), "SOURCE_ITEM_NOT_OBJECT")
        require(published_date(item.get("stat_date")) == d, "SOURCE_DATE_MISMATCH")
        level = item.get("cnt_level")
        require(type(level) is int and level in levels, "SOURCE_LEVEL_INVALID")
        levels[level] += 1
        if level == 2:
            require(national is None and item.get("cnt_name") == "Российская Федерация",
                    "NATIONAL_ROW_INVALID")
            national = item
            continue
        if level == 1:
            continue
        code = item.get("ssrf")
        label = item.get("name")
        require(isinstance(code, str) and re.fullmatch(r"\d{1,3}", code),
                "REGION_CODE_INVALID")
        require(isinstance(label, str) and bool(label.strip()) and
                label == item.get("cnt_name") and
                not any(ord(ch) < 32 for ch in label), "REGION_NAME_INVALID")
        require(code not in rows, "REGION_DUPLICATE")
        vals = [counter(item.get(key)) for key in SOURCE_COLUMNS[2:]]
        require(int(vals[0]) == int(item["cnt_ul_total"]) + int(item["cnt_ip_total"]),
                "SOURCE_TOTAL_INCONSISTENT")
        require(int(item["cnt_ul_total"]) ==
                sum(int(vals[i]) for i in (1, 2, 3)), "SOURCE_UL_INCONSISTENT")
        require(int(item["cnt_ip_total"]) ==
                sum(int(vals[i]) for i in (4, 5, 6)), "SOURCE_IP_INCONSISTENT")
        rows[code] = (code, label, *vals)
    require(levels[2] == 1 and levels[1] >= 8 and 80 <= levels[0] <= 120,
            "SOURCE_COVERAGE_INVALID")
    require(national is not None and
            int(counter(national.get("cnt_total"))) ==
            int(counter(national.get("cnt_ul_total"))) +
            int(counter(national.get("cnt_ip_total"))),
            "SOURCE_NATIONAL_TOTAL_INVALID")
    return rows


def write_csv(rows):
    with io.StringIO(newline="") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(rows[k] for k in sorted(rows))
        return output.getvalue().encode("utf-8")


def read_csv(blob):
    try:
        text = blob.decode("utf-8")
        with io.StringIO(text, newline="") as fp:
            reader = csv.reader(fp, strict=True)
            require(tuple(next(reader)) == COLUMNS, "CSV_HEADER_INVALID")
            rows = {}
            for row in reader:
                require(len(row) == len(COLUMNS), "CSV_WIDTH_INVALID")
                code, label, *vals = row
                require(re.fullmatch(r"\d{1,3}", code) is not None and
                        code not in rows and bool(label) and
                        not any(ord(ch) < 32 for ch in label), "CSV_REGION_INVALID")
                for val in vals:
                    counter(val)
                rows[code] = tuple(row)
            require(80 <= len(rows) <= 120, "CSV_ROWS_INVALID")
            return rows
    except (UnicodeError, csv.Error, StopIteration):
        raise FnsError("CSV_INVALID") from None


def compare(existing, candidate):
    """Return NEW/UPDATED/NO_CHANGE and number of materially changed regions."""
    newer = read_csv(candidate)
    if existing is None:
        return "NEW", len(newer)
    older = read_csv(existing)
    require(len(newer) >= int(len(older) * 0.90),
            "SOURCE_REGION_DROP_UNEXPECTED")
    changed = sum(older.get(k) != newer.get(k) for k in older.keys() | newer.keys())
    return ("UPDATED" if changed else "NO_CHANGE"), changed


def capture(d):
    body = urlencode({"statDate": format_source_date(d)}).encode("ascii")
    raw = get_official(SOURCE_JSON, data=body)
    data = write_csv(decode_snapshot(raw, d))
    require(read_csv(data), "EMPTY_CSV")
    return data, hashlib.sha256(raw).hexdigest()


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("discover", "capture", "validate", "compare", "backfill"))
    parser.add_argument("--date")
    parser.add_argument("--file")
    parser.add_argument("--against")
    parser.add_argument("--output-dir")
    parser.add_argument("--from-date")
    parser.add_argument("--to-date")
    args = parser.parse_args(argv)
    try:
        if args.mode == "discover":
            print("\n".join(d.isoformat() for d in discover_dates()))
        elif args.mode == "validate":
            require(args.file is not None, "FILE_REQUIRED")
            print("VALID", len(read_csv(Path(args.file).read_bytes())))
        elif args.mode == "compare":
            require(args.file is not None, "FILE_REQUIRED")
            other = Path(args.against).read_bytes() if args.against else None
            print(*compare(other, Path(args.file).read_bytes()))
        else:
            require(args.output_dir is not None, "OUTPUT_DIR_REQUIRED")
            if args.mode == "capture":
                require(args.date is not None, "DATE_REQUIRED")
                dates = [iso_to_date(args.date)]
            else:
                require(args.from_date is not None and args.to_date is not None,
                        "BACKFILL_RANGE_REQUIRED")
                start, end = iso_to_date(args.from_date), iso_to_date(args.to_date)
                dates = [d for d in discover_dates() if start <= d <= end]
                require(0 < len(dates) <= 15, "BACKFILL_BATCH_LIMIT")
            for d in dates:
                require(d in discover_dates(), "DATE_NOT_PUBLISHED")
                data, source_sha = capture(d)
                target = Path(args.output_dir) / str(d.year) / file_for(d).name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                print("CAPTURED", d.isoformat(), len(read_csv(data)),
                      hashlib.sha256(data).hexdigest(), source_sha)
        return 0
    except FnsError as e:
        print("FNS_ERROR", e)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
