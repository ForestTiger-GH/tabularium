#!/usr/bin/env python3
"""Byte-level monitoring of official XLSX files; no external dependencies."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
from html import escape as html_escape, unescape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "registry.json"
STATE = ROOT / "state.json"
ID_RE = re.compile(r"[A-Za-z0-9_-]+\Z")
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
MAX_HTML = 10 * 1024 * 1024
MAX_XLSX = 100 * 1024 * 1024
MAX_UNCOMPRESSED = 500 * 1024 * 1024
MAX_ZIP_MEMBERS = 4000
TIMEOUT = 20
ATTEMPTS = 2
TRANSFER_BUDGET = 90
MOSCOW = timezone(timedelta(hours=3))
# These are deliberately source-specific: redirects may not escape an official host.
HOSTS = {
    "Bank of Russia": {"www.cbr.ru", "cbr.ru"},
    "Ministry of Finance of Russia": {"minfin.gov.ru"},
}


class MonitorError(Exception):
    """Safe, non-secret diagnostic code."""


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self.hrefs.extend(value for key, value in attrs
                              if key.lower() == "href" and value)


def now_utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MonitorError("JSON_READ_FAILED") from exc
    if not isinstance(data, dict):
        raise MonitorError("JSON_OBJECT_REQUIRED")
    return data


def validate_url(url, publisher, *, purpose):
    if not isinstance(url, str):
        raise MonitorError("URL_INVALID")
    try:
        parsed = urllib.parse.urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise MonitorError("URL_INVALID") from exc
    if (parsed.scheme != "https" or parsed.hostname not in HOSTS.get(publisher, set())
            or port not in (None, 443) or parsed.username or parsed.password
            or parsed.query or parsed.fragment or "\\" in url):
        raise MonitorError("URL_UNAPPROVED")
    path = urllib.parse.unquote(parsed.path)
    if publisher == "Bank of Russia":
        allowed = (path.startswith("/vfs/statistics/") or
                   path.startswith("/Content/Document/File/"))
        if purpose != "file" or not allowed or not path.lower().endswith(".xlsx"):
            raise MonitorError("URL_PATH_UNAPPROVED")
    elif publisher == "Ministry of Finance of Russia":
        if purpose == "page":
            allowed = path == "/ru/statistics/fedbud/execute/"
        else:
            allowed = (path.startswith("/common/upload/library/") and
                       path.lower().endswith(".xlsx"))
        if not allowed:
            raise MonitorError("URL_PATH_UNAPPROVED")
    else:
        raise MonitorError("PUBLISHER_UNAPPROVED")
    return url


def load_registry(path=REGISTRY):
    document = read_json(path)
    if set(document) != {"version", "sources"} or document["version"] != 1:
        raise MonitorError("REGISTRY_SCHEMA_INVALID")
    sources = document["sources"]
    if not isinstance(sources, list):
        raise MonitorError("REGISTRY_SCHEMA_INVALID")
    seen = set()
    for item in sources:
        if not isinstance(item, dict):
            raise MonitorError("REGISTRY_ITEM_INVALID")
        kind = item.get("kind")
        expected = ({"id", "publisher", "title", "kind", "enabled", "url"}
                    if kind == "direct" else
                    {"id", "publisher", "title", "kind", "enabled", "page_url",
                     "file_stem", "file_suffix"} if kind == "page_attachment" else set())
        if set(item) != expected:
            raise MonitorError("REGISTRY_ITEM_SCHEMA_INVALID")
        ident = item["id"]
        if not isinstance(ident, str) or not ID_RE.fullmatch(ident) or ident in seen:
            raise MonitorError("REGISTRY_ID_INVALID_OR_DUPLICATE")
        seen.add(ident)
        if (not isinstance(item["publisher"], str) or
                item["publisher"] not in HOSTS or
                not isinstance(item["title"], str) or
                not item["title"].strip() or type(item["enabled"]) is not bool):
            raise MonitorError("REGISTRY_ITEM_INVALID")
        if kind == "direct":
            validate_url(item["url"], item["publisher"], purpose="file")
        else:
            validate_url(item["page_url"], item["publisher"], purpose="page")
            if (not isinstance(item["file_stem"], str) or
                    not item["file_stem"] or
                    not isinstance(item["file_suffix"], str) or
                    not item["file_suffix"].lower().endswith(".xlsx")):
                raise MonitorError("ATTACHMENT_MATCHER_INVALID")
    return sources


def load_state(path=STATE):
    document = read_json(path)
    if set(document) != {"version", "items"} or document["version"] != 1 or not isinstance(document["items"], dict):
        raise MonitorError("STATE_SCHEMA_INVALID")
    for key, item in document["items"].items():
        if (not ID_RE.fullmatch(key) or not isinstance(item, dict) or
                set(item) != {"sha256", "first_seen_at", "last_change_at", "resolved_url"} or
                not isinstance(item["sha256"], str) or not SHA_RE.fullmatch(item["sha256"]) or
                not isinstance(item["first_seen_at"], str) or
                not isinstance(item["resolved_url"], str) or
                (item["last_change_at"] is not None and not isinstance(item["last_change_at"], str))):
            raise MonitorError("STATE_ITEM_INVALID")
    return document


def save_state(document, path=STATE):
    payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    handle = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=path.parent, prefix=".monitor-state-",
                                         delete=False) as fp:
            handle = fp.name
            fp.write(payload)
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(handle, path)
    finally:
        if handle and os.path.exists(handle):
            os.unlink(handle)


class RedirectGuard(urllib.request.HTTPRedirectHandler):
    def __init__(self, validator):
        self.validator = validator

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.validator(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_source(url, publisher, purpose):
    checker = lambda value: validate_url(value, publisher, purpose=purpose)
    checker(url)
    opener = urllib.request.build_opener(RedirectGuard(checker))
    request = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; TabulariumPublicationMonitor/1.0)",
        "Accept": "text/html" if purpose == "page" else
                  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream",
        "Accept-Encoding": "identity",
    })
    for attempt in range(ATTEMPTS):
        try:
            response = opener.open(request, timeout=TIMEOUT)
            checker(response.geturl())
            if response.status != 200:
                response.close()
                raise MonitorError("SOURCE_HTTP_UNEXPECTED")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                response.close()
                raise MonitorError("SOURCE_ENCODING_UNEXPECTED")
            return response
        except urllib.error.HTTPError as exc:
            code = exc.code
            exc.close()
            if attempt + 1 == ATTEMPTS or code not in (429, 500, 502, 503, 504):
                raise MonitorError(f"SOURCE_HTTP_{code}") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt + 1 == ATTEMPTS:
                raise MonitorError("SOURCE_NETWORK_FAILED") from None
        if attempt + 1 < ATTEMPTS:
            time.sleep(1 + attempt)
    raise MonitorError("SOURCE_NETWORK_FAILED")


def read_limited(response, cap):
    try:
        length = response.headers.get("Content-Length")
        if length and (not length.isdecimal() or int(length) > cap):
            raise MonitorError("SOURCE_SIZE_LIMIT")
        pieces = []
        count = 0
        start = time.monotonic()
        while True:
            if time.monotonic() - start > TRANSFER_BUDGET:
                raise MonitorError("SOURCE_TRANSFER_TIMEOUT")
            chunk = response.read(min(65536, cap - count + 1))
            if not chunk:
                break
            count += len(chunk)
            if count > cap:
                raise MonitorError("SOURCE_SIZE_LIMIT")
            pieces.append(chunk)
        if length and count != int(length):
            raise MonitorError("SOURCE_TRUNCATED")
        return b"".join(pieces)
    except (OSError, TimeoutError) as exc:
        raise MonitorError("SOURCE_READ_FAILED") from exc


def resolve_attachment(item, page_cache):
    page_url = item["page_url"]
    if page_url not in page_cache:
        try:
            with open_source(page_url, item["publisher"], "page") as response:
                mime = response.headers.get_content_type().lower()
                if mime not in ("text/html", "application/xhtml+xml"):
                    raise MonitorError("PAGE_NOT_HTML")
                raw = read_limited(response, MAX_HTML)
                charset = response.headers.get_content_charset() or "utf-8"
            try:
                page = raw.decode(charset)
            except (LookupError, UnicodeError) as exc:
                raise MonitorError("PAGE_DECODE_FAILED") from exc
            parser = Links()
            parser.feed(page)
            if not parser.hrefs:
                raise MonitorError("PAGE_WITHOUT_LINKS")
            page_cache[page_url] = parser.hrefs
        except MonitorError as exc:
            page_cache[page_url] = exc
    links = page_cache[page_url]
    if isinstance(links, MonitorError):
        raise links
    candidates = set()
    for href in links:
        absolute = urllib.parse.urljoin(page_url, unescape(href.strip()))
        parsed = urllib.parse.urlsplit(absolute)
        basename = urllib.parse.unquote(parsed.path.rsplit("/", 1)[-1])
        if (not basename.lower().startswith(item["file_stem"].lower()) or
                not basename.lower().endswith(item["file_suffix"].lower())):
            continue
        # Encode Unicode and spaces without double-encoding existing percent escapes.
        clean_path = urllib.parse.quote(urllib.parse.unquote(parsed.path), safe="/-._~")
        candidate = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc,
                                             clean_path, parsed.query, parsed.fragment))
        validate_url(candidate, item["publisher"], purpose="file")
        candidates.add(candidate)
    if len(candidates) != 1:
        raise MonitorError("ATTACHMENT_NOT_FOUND" if not candidates else "ATTACHMENT_AMBIGUOUS")
    return next(iter(candidates))


def resolve(item, page_cache):
    return item["url"] if item["kind"] == "direct" else resolve_attachment(item, page_cache)


def verify_xlsx(path):
    try:
        with path.open("rb") as fp:
            if fp.read(4) != b"PK\x03\x04":
                raise MonitorError("XLSX_SIGNATURE_INVALID")
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if (len(infos) > MAX_ZIP_MEMBERS or
                    sum(info.file_size for info in infos) > MAX_UNCOMPRESSED or
                    len(names) != len(set(names)) or
                    "[Content_Types].xml" not in names or
                    "xl/workbook.xml" not in names or
                    any(info.flag_bits & 1 for info in infos)):
                raise MonitorError("XLSX_STRUCTURE_INVALID")
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise MonitorError("XLSX_CORRUPT") from exc


def download_hash(url, publisher):
    file_name = None
    count = 0
    sha = hashlib.sha256()
    try:
        with tempfile.NamedTemporaryFile(prefix="tabularium-monitor-", suffix=".xlsx", delete=False) as tmp:
            file_name = tmp.name
            with open_source(url, publisher, "file") as response:
                final_url = response.geturl()
                mime = response.headers.get_content_type().lower()
                if mime in ("text/html", "application/xhtml+xml", "application/json", "text/plain"):
                    raise MonitorError("SOURCE_NOT_XLSX")
                length = response.headers.get("Content-Length")
                if length and (not length.isdecimal() or int(length) > MAX_XLSX):
                    raise MonitorError("SOURCE_SIZE_LIMIT")
                start = time.monotonic()
                while True:
                    if time.monotonic() - start > TRANSFER_BUDGET:
                        raise MonitorError("SOURCE_TRANSFER_TIMEOUT")
                    try:
                        chunk = response.read(65536)
                    except (OSError, TimeoutError) as exc:
                        raise MonitorError("SOURCE_READ_FAILED") from exc
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > MAX_XLSX:
                        raise MonitorError("SOURCE_SIZE_LIMIT")
                    tmp.write(chunk)
                    sha.update(chunk)
                if length and count != int(length):
                    raise MonitorError("SOURCE_TRUNCATED")
        if count < 512:
            raise MonitorError("SOURCE_TOO_SMALL")
        verify_xlsx(Path(file_name))
        return sha.hexdigest(), final_url, count
    finally:
        if file_name:
            Path(file_name).unlink(missing_ok=True)


def send_telegram(token, chat_id, text, thread_id=None):
    if not token or not chat_id:
        raise MonitorError("TELEGRAM_NOT_CONFIGURED")
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML",
               "disable_web_page_preview": True}
    if thread_id:
        if not str(thread_id).isdigit():
            raise MonitorError("TELEGRAM_THREAD_INVALID")
        payload["message_thread_id"] = int(thread_id)
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept-Encoding": "identity"},
        method="POST",
    )
    def reject_redirect(url):
        raise MonitorError("TELEGRAM_REDIRECT_REJECTED")

    opener = urllib.request.build_opener(RedirectGuard(reject_redirect))
    try:
        with opener.open(req, timeout=TIMEOUT) as response:
            raw = response.read(16 * 1024)
            if response.status != 200:
                raise MonitorError("TELEGRAM_HTTP_FAILED")
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get("ok") is not True:
            raise MonitorError("TELEGRAM_REJECTED")
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        raise MonitorError(f"TELEGRAM_HTTP_{status}") from None
    except (urllib.error.URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError):
        raise MonitorError("TELEGRAM_DELIVERY_UNKNOWN") from None


def format_alert(item, url, observed_at):
    date = datetime.fromisoformat(observed_at.replace("Z", "+00:00")).astimezone(MOSCOW)
    return ("📊 <b>ИЗМЕНЕНИЕ ФАЙЛА ИСТОЧНИКА</b>\n\n"
            f"<b>{html_escape(item['publisher'])}</b>\n"
            f"{html_escape(item['title'])}\n\n"
            f"Обнаружено: {date:%d.%m.%Y %H:%M} МСК\n"
            "Изменились байты исходного XLSX относительно предыдущей проверки.\n"
            f"<a href=\"{html_escape(url, quote=True)}\">Открыть исходный файл</a>")


def run_scan(mode, *, registry=REGISTRY, state_path=STATE, token=None, chat_id=None,
             thread_id=None, dry_run=False):
    sources = load_registry(registry)
    document = load_state(state_path)
    if mode == "check" and not dry_run and (not token or not chat_id):
        raise MonitorError("TELEGRAM_NOT_CONFIGURED")
    stats = {"BASELINE_CREATED": 0, "UNCHANGED": 0, "CHANGED": 0,
             "CHECK_FAILED": 0, "SKIPPED": 0}
    page_cache = {}
    for item in sources:
        ident = item["id"]
        if not item["enabled"] or (mode == "bootstrap" and ident in document["items"]):
            stats["SKIPPED"] += 1
            continue
        try:
            url = resolve(item, page_cache)
            digest, effective_url, count = download_hash(url, item["publisher"])
            previous = document["items"].get(ident)
            if previous is None:
                stats["BASELINE_CREATED"] += 1
                print(f"BASELINE_CREATED {ident} {count}B")
                if not dry_run:
                    document["items"][ident] = {
                        "sha256": digest, "first_seen_at": now_utc(),
                        "last_change_at": None, "resolved_url": effective_url}
                    save_state(document, state_path)
            elif previous["sha256"] == digest:
                stats["UNCHANGED"] += 1
                print(f"UNCHANGED {ident}")
            elif mode == "bootstrap":
                stats["SKIPPED"] += 1
            else:
                stats["CHANGED"] += 1
                print(f"CHANGED {ident}")
                if not dry_run:
                    stamp = now_utc()
                    send_telegram(token, chat_id, format_alert(item, effective_url, stamp), thread_id)
                    document["items"][ident] = {
                        "sha256": digest, "first_seen_at": previous["first_seen_at"],
                        "last_change_at": stamp, "resolved_url": effective_url}
                    save_state(document, state_path)
        except MonitorError as exc:
            stats["CHECK_FAILED"] += 1
            print(f"CHECK_FAILED {ident} {exc}")
    print("SUMMARY " + " ".join(f"{k}={v}" for k, v in stats.items()))
    return 1 if stats["CHECK_FAILED"] else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("validate", "bootstrap", "check", "test-telegram"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.mode == "validate":
            sources = load_registry()
            state = load_state()
            print(f"VALID registry={len(sources)} state={len(state['items'])}")
            return 0
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        thread_id = os.environ.get("TELEGRAM_THREAD_ID")
        if args.mode == "test-telegram":
            if args.dry_run:
                raise MonitorError("DRY_RUN_NOT_SUPPORTED")
            send_telegram(token, chat_id,
                          "🧪 <b>Tabularium Monitor</b> — тестовое сообщение. "
                          "Мониторинг по расписанию ещё не включён.", thread_id)
            print("TELEGRAM_TEST_SENT")
            return 0
        return run_scan(args.mode, token=token, chat_id=chat_id,
                        thread_id=thread_id, dry_run=args.dry_run)
    except MonitorError as exc:
        print(f"MONITOR_ERROR {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
