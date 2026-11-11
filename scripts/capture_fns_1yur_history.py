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
        if len(set(candidates)) != 1:
            raise HistoryError("SOURCE_ASSET_MISSING_OR_AMBIGUOUS:" + day.isoformat())
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
