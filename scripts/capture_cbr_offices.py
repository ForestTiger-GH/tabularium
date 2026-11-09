#!/usr/bin/env python3
"""Source-faithful, fail-closed CBR offices snapshots; no third-party packages."""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
from html.parser import HTMLParser
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SOURCE_URL = "https://www.cbr.ru/banking_sector/credit/cstat/"
REPO = "ForestTiger-GH/tabularium"
BRANCH = "main"
CORPUS_ROOT = "scrolls/russia/authorities/bank-of-russia/credit-institution-structural-units"
TZ = timezone(timedelta(hours=4))
CSV_COLUMNS = ("source_row", "section_label", "region", "organization_name",
               "registration_number", "indicator_column", "indicator_name",
               "raw_value", "value_state")
DATE_NAME = re.compile(r"OFFICES_(\d{4}-\d{2}-\d{2})\.csv\Z", re.ASCII)
HASH = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
COMMIT_HASH = re.compile(r"[0-9a-f]{40}\Z", re.ASCII)
MAX_HTML = 10 * 1024 * 1024
MAX_CSV = 10 * 1024 * 1024
MAX_NODES = 180_000
MAX_ROWS = 30_000
MAX_CELLS = 150_000
# Source note is outside the table and is not archived in daily CSVs.
KNOWN_CONTEXT = ("Порядок следования федеральных округов задан в соответствии с "
                 "Общероссийским классификатором экономических регионов (ОКЭР).")


class CaptureError(Exception):
    """A named, non-recoverable failure. No publishing follows this exception."""


def fail(code: str) -> None:
    raise CaptureError(code)


def clean_text(value: str) -> str:
    # Layout whitespace only; preserve all substantive characters, punctuation and digits.
    value = re.sub(r"\s+", " ", value).strip()
    if any((ord(c) < 32 or 127 <= ord(c) <= 159) for c in value) or "\ufffd" in value:
        fail("SOURCE_CONTROL_CHARACTER")
    return value


def validate_url(url: str) -> None:
    p = urllib.parse.urlsplit(url)
    if (p.scheme != "https" or p.hostname not in ("www.cbr.ru", "cbr.ru")
            or p.port not in (None, 443) or p.username or p.password
            or p.path != "/banking_sector/credit/cstat/" or p.query or p.fragment):
        fail("SOURCE_REDIRECT_REJECTED")


class StrictRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)  # before urllib opens the redirected address
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_source_html() -> tuple[str, datetime]:
    opener = urllib.request.build_opener(StrictRedirect())
    request = urllib.request.Request(SOURCE_URL, headers={
        "User-Agent": "Tabularium-CBR-Offices/1.0 (+https://github.com/ForestTiger-GH/tabularium)",
        "Accept": "text/html", "Accept-Encoding": "identity"})
    for attempt in range(3):
        try:
            with opener.open(request, timeout=18) as response:
                validate_url(response.geturl())
                if response.status != 200:
                    fail("SOURCE_HTTP_STATUS")
                mime = response.headers.get_content_type().lower()
                if mime not in ("text/html", "application/xhtml+xml"):
                    fail("SOURCE_MIME_INVALID")
                if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                    fail("SOURCE_ENCODING_UNEXPECTED")
                length = response.headers.get("Content-Length")
                if length is not None and (not length.isdecimal() or int(length) > MAX_HTML):
                    fail("SOURCE_SIZE_LIMIT")
                body = response.read(MAX_HTML + 1)
                observed_at = datetime.now(TZ)  # fixed immediately after full response read
                if len(body) > MAX_HTML:
                    fail("SOURCE_SIZE_LIMIT")
                if length is not None and len(body) != int(length):
                    fail("SOURCE_TRUNCATED")
                if not body:
                    fail("SOURCE_EMPTY")
                charset = response.headers.get_content_charset() or "utf-8"
                try:
                    decoded = body.decode(charset, errors="strict")
                except (UnicodeError, LookupError):
                    fail("SOURCE_CHARSET_INVALID")
                if "\ufffd" in decoded or "\x00" in decoded:
                    fail("SOURCE_CHARSET_INVALID")
                return decoded, observed_at
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            fail(f"FETCH_HTTP_{exc.code}")
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            fail("FETCH_NETWORK_FAILED")
    fail("FETCH_FAILED")


class Cell:
    def __init__(self, tag: str, attrs: dict[str, str]):
        self.tag = tag
        self.attrs = attrs
        self.fragments: list[str] = []
        self.colspan = self._span("colspan")
        self.rowspan = self._span("rowspan")

    def _span(self, key: str) -> int:
        raw = self.attrs.get(key, "1")
        if not re.fullmatch(r"[0-9]{1,3}", raw):
            fail("SOURCE_SPAN_INVALID")
        n = int(raw)
        if not 1 <= n <= 40:
            fail("SOURCE_SPAN_INVALID")
        return n

    @property
    def text(self) -> str:
        return clean_text("".join(self.fragments))


class Table:
    def __init__(self):
        self.rows: list[list[Cell]] = []
        self.row: list[Cell] | None = None
        self.cell: Cell | None = None
        self.in_header = False
        self.header_rows: set[int] = set()


class SourceScanner(HTMLParser):
    """Finite, non-executing table scanner (not a browser or script evaluator)."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables: list[Table] = []
        self.table: Table | None = None
        self.outside_text: list[str] = []
        self.ignored_depth = 0
        self.nodes = 0
        self.cells = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        self.nodes += 1
        if self.nodes > MAX_NODES:
            fail("SOURCE_DOM_LIMIT")
        if tag in ("script", "style", "template", "noscript") and self.table is None:
            self.ignored_depth += 1
        if tag == "table":
            if self.table is not None:
                fail("SOURCE_NESTED_TABLE")
            self.table = Table()
        if self.table is None:
            return
        if tag == "thead":
            self.table.in_header = True
        elif tag == "tr":
            if self.table.row is not None:
                fail("SOURCE_TR_UNCLOSED")
            self.table.row = []
        elif tag in ("td", "th"):
            if self.table.row is None or self.table.cell is not None:
                fail("SOURCE_CELL_STRUCTURE")
            attrs_dict = {k: v or "" for k, v in attrs}
            self.table.cell = Cell(tag, attrs_dict)
            self.cells += 1
            if self.cells > MAX_CELLS:
                fail("SOURCE_CELL_LIMIT")
        elif tag == "br" and self.table.cell is not None:
            self.table.cell.fragments.append(" ")

    def handle_data(self, data: str):
        if self.table is not None:
            if self.table.cell is not None:
                self.table.cell.fragments.append(data)
        elif data.strip() and self.ignored_depth == 0:
            self.outside_text.append(data)

    def handle_endtag(self, tag: str):
        if self.table is None:
            if tag in ("script", "style", "template", "noscript") and self.ignored_depth:
                self.ignored_depth -= 1
            return
        if tag in ("td", "th"):
            if self.table.cell is None or self.table.cell.tag != tag:
                fail("SOURCE_CELL_UNCLOSED")
            assert self.table.row is not None
            self.table.row.append(self.table.cell)
            self.table.cell = None
        elif tag == "tr":
            if self.table.row is None or self.table.cell is not None:
                fail("SOURCE_TR_INVALID")
            if len(self.table.rows) >= MAX_ROWS:
                fail("SOURCE_ROW_LIMIT")
            self.table.rows.append(self.table.row)
            if self.table.in_header:
                self.table.header_rows.add(len(self.table.rows))
            self.table.row = None
        elif tag == "thead":
            self.table.in_header = False
        elif tag == "table":
            if self.table.cell is not None or self.table.row is not None:
                fail("SOURCE_TABLE_UNCLOSED")
            self.tables.append(self.table)
            self.table = None

    def close(self):
        super().close()
        if self.table is not None:
            fail("SOURCE_TABLE_UNCLOSED")


def expanded_grid(rows: list[list[Cell]], width: int | None = None) -> list[list[Cell]]:
    pending: dict[int, tuple[Cell, int]] = {}
    result: list[list[Cell]] = []
    for row in rows:
        assigned: dict[int, Cell] = {}
        next_pending: dict[int, tuple[Cell, int]] = {}
        for index, (cell, remaining) in pending.items():
            assigned[index] = cell
            if remaining > 1:
                next_pending[index] = (cell, remaining - 1)
        col = 0
        for cell in row:
            while col in assigned:
                col += 1
            for i in range(col, col + cell.colspan):
                if i in assigned or i >= 40:
                    fail("SOURCE_SPAN_OVERLAP")
                assigned[i] = cell
                if cell.rowspan > 1:
                    next_pending[i] = (cell, cell.rowspan - 1)
            col += cell.colspan
        if not assigned:
            fail("SOURCE_EMPTY_ROW")
        n = max(assigned) + 1
        if set(assigned) != set(range(n)) or (width is not None and n != width):
            fail("SOURCE_GRID_MISALIGNMENT")
        result.append([assigned[i] for i in range(n)])
        pending = next_pending
    if pending:
        fail("SOURCE_ROWSPAN_OVERRUN")
    return result


def header_identity(text: str) -> str:
    return re.sub(r"\s+", "", text).casefold().replace("ё", "е").replace(".", "")


def identify_header(table: Table) -> tuple[int, list[str]] | None:
    # Try the first one to four physical rows; multi-level headers use distinct hierarchy.
    for n in range(1, min(4, len(table.rows)) + 1):
        try:
            grid = expanded_grid(table.rows[:n])
        except CaptureError:
            continue
        if any(len(r) != len(grid[-1]) for r in grid):
            continue
        names: list[str] = []
        for col in range(len(grid[-1])):
            parts: list[str] = []
            for row in grid:
                value = row[col].text
                if value and (not parts or parts[-1] != value):
                    parts.append(value)
            names.append(" / ".join(parts))
        keys = [header_identity(x) for x in names]
        basic = ("регион", "наименованиеко", "рег№ко")
        if len(names) < 4 or keys[:3] != list(basic):
            continue
        if any(not v for v in names[3:]):
            fail("SOURCE_HEADER_AMBIGUOUS")
        # Never include an actual data row in the identified header.
        if any(not any(c.tag == "th" for c in row) for row in table.rows[:n]) and n > 1:
            continue
        return n, names
    return None


def extract_records(html: str) -> tuple[list[tuple[str, ...]], int]:
    parser = SourceScanner()
    try:
        parser.feed(html)
        parser.close()
    except (ValueError, RecursionError):
        fail("SOURCE_DOM_INVALID")
    note = clean_text(" ".join(parser.outside_text))
    if KNOWN_CONTEXT not in note:
        fail("SOURCE_CONTEXT_CHANGED")
    candidates = [(t, h) for t in parser.tables if (h := identify_header(t)) is not None]
    if len(candidates) != 1:
        fail("SOURCE_TABLE_AMBIGUOUS")
    table, (header_count, header) = candidates[0]
    width = len(header)
    if table.header_rows and set(range(1, header_count + 1)) != table.header_rows:
        fail("SOURCE_HEADER_LAYOUT_CHANGED")
    # Column names must not collapse the identity or duplicate distinct indicators.
    if len({header_identity(x) for x in header[3:]}) != width - 3:
        fail("SOURCE_HEADER_DUPLICATE")
    rows = table.rows[header_count:]
    # Data may have rowspan, so expand all data physical rows as a single grid.
    # Section rows are a separate structural type and never inherit rowspan.
    current_section = ""
    extracted: list[tuple[str, ...]] = []
    data_rows = 0
    pending_rows: list[tuple[int, list[Cell]]] = []

    def flush():
        nonlocal data_rows, pending_rows
        if not pending_rows:
            return
        grid = expanded_grid([r for _, r in pending_rows], width)
        for (row_index, _), cells in zip(pending_rows, grid):
            if any(not cells[i].text for i in range(3)):
                fail("SOURCE_IDENTIFIER_MISSING")
            data_rows += 1
            for col in range(3, width):
                value = cells[col].text
                extracted.append((str(row_index), current_section, cells[0].text,
                                  cells[1].text, cells[2].text, str(col + 1),
                                  header[col], value, "present" if value else "blank"))
        pending_rows = []

    for physical_index, cells in enumerate(rows, header_count + 1):
        if not cells:
            fail("SOURCE_EMPTY_ROW")
        if len(cells) == 1 and cells[0].colspan == width and cells[0].rowspan == 1:
            flush()
            if cells[0].text:
                current_section = cells[0].text
            # Empty full-width structural separators are explicitly supported.
            continue
        if any(c.colspan != 1 for c in cells):
            fail("SOURCE_DATA_COLSPAN_AMBIGUOUS")
        pending_rows.append((physical_index, cells))
    flush()
    if data_rows == 0 or len(extracted) != data_rows * (width - 3):
        fail("SOURCE_INCOMPLETE")
    return extracted, data_rows


def serialize_csv(records: list[tuple[str, ...]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    writer.writerows(records)
    return buffer.getvalue().encode("utf-8", "strict")


def validate_csv_bytes(data: bytes) -> tuple[int, int]:
    if not data or len(data) > MAX_CSV or data.startswith(b"\xef\xbb\xbf"):
        fail("CSV_SIZE_OR_BOM")
    try:
        content = data.decode("utf-8", "strict")
        rows = list(csv.reader(io.StringIO(content, newline=""), strict=True))
    except (UnicodeError, csv.Error):
        fail("CSV_INVALID_ENCODING")
    if not rows or tuple(rows[0]) != CSV_COLUMNS or len(rows) < 2:
        fail("CSV_HEADER_OR_EMPTY")
    previous_row = 0
    previous_col = 0
    indicator_map: dict[int, str] = {}
    grouped: dict[int, set[int]] = {}
    last_id: tuple[str, ...] | None = None
    for row in rows[1:]:
        if len(row) != 9:
            fail("CSV_COLUMN_COUNT")
        for value in row:
            clean_text(value)  # reject controls, but preserve accepted CSV text unchanged
        src, section, region, org, reg, col, indicator, value, state = row
        if not src.isascii() or not src.isdecimal() or not col.isascii() or not col.isdecimal():
            fail("CSV_INDEX_INVALID")
        source_row, column = int(src), int(col)
        if not 1 <= source_row <= MAX_ROWS or not 4 <= column <= 40:
            fail("CSV_INDEX_INVALID")
        if source_row < previous_row or (source_row == previous_row and column <= previous_col):
            fail("CSV_ORDER_INVALID")
        if not region or not org or not reg or not indicator:
            fail("CSV_IDENTIFIERS_INVALID")
        if (state != ("present" if value else "blank")):
            fail("CSV_VALUE_STATE_INVALID")
        identity = (section, region, org, reg)
        if source_row == previous_row and last_id != identity:
            fail("CSV_ROW_IDENTITY_INVALID")
        if column in indicator_map and indicator_map[column] != indicator:
            fail("CSV_INDICATOR_MISMATCH")
        indicator_map[column] = indicator
        if column in grouped.setdefault(source_row, set()):
            fail("CSV_DUPLICATE_CELL")
        grouped[source_row].add(column)
        previous_row, previous_col, last_id = source_row, column, identity
    expected = set(range(4, max(indicator_map) + 1))
    if any(set(cols) != expected for cols in grouped.values()):
        fail("CSV_MISSING_INDICATOR")
    if serialize_csv([tuple(x) for x in rows[1:]]) != data:
        fail("CSV_NON_CANONICAL")
    return len(grouped), len(rows) - 1


def filename_for(observed_at: datetime) -> str:
    return "OFFICES_" + observed_at.astimezone(TZ).date().isoformat() + ".csv"


def file_date(name: str) -> date:
    m = DATE_NAME.fullmatch(name)
    if not m:
        fail("ARTIFACT_FILENAME_INVALID")
    try:
        d = date.fromisoformat(m.group(1))
    except ValueError:
        fail("ARTIFACT_DATE_INVALID")
    if d.isoformat() != m.group(1):
        fail("ARTIFACT_DATE_INVALID")
    return d


def capture(output_dir: Path, github_output: Path | None = None) -> Path:
    html, observed_at = fetch_source_html()
    records, source_rows = extract_records(html)
    data = serialize_csv(records)
    _, count = validate_csv_bytes(data)
    if not output_dir.is_dir() or any(output_dir.iterdir()):
        fail("CAPTURE_OUTPUT_DIR_NOT_EMPTY")
    target = output_dir / filename_for(observed_at)
    with target.open("xb") as stream:
        stream.write(data)
    digest = hashlib.sha256(data).hexdigest()
    if github_output is not None:
        with github_output.open("a", encoding="ascii", newline="\n") as stream:
            stream.write(f"csv_sha256={digest}\n")
    print(f"CAPTURED date={observed_at.date()} source_rows={source_rows} observations={count} sha256={digest}")
    return target


def validate_artifact(directory: Path, expected_sha: str) -> tuple[str, bytes]:
    if not HASH.fullmatch(expected_sha):
        fail("ARTIFACT_EXPECTED_HASH_INVALID")
    if directory.is_symlink() or not directory.is_dir():
        fail("ARTIFACT_DIRECTORY_INVALID")
    entries = list(directory.iterdir())
    if len(entries) != 1:
        fail("ARTIFACT_FILE_COUNT")
    file = entries[0]
    if file.is_symlink() or not file.is_file() or file.stat().st_nlink != 1:
        fail("ARTIFACT_FILE_TYPE")
    file_date(file.name)
    if file.stat().st_size > MAX_CSV:
        fail("ARTIFACT_SIZE")
    data = file.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha:
        fail("ARTIFACT_HASH_MISMATCH")
    validate_csv_bytes(data)
    return file.name, data


def git(*args: str, allow_failure: bool = False) -> subprocess.CompletedProcess[bytes]:
    p = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=40, check=False)
    if p.returncode and not allow_failure:
        fail("GIT_COMMAND_FAILED_" + args[0].upper().replace("-", "_"))
    return p


def git_text(*args: str) -> str:
    return git(*args).stdout.decode("ascii", "strict").strip()


def assert_git_context(repo_root: Path, code_commit: str, strict_remote: bool = True):
    if Path.cwd().resolve() != repo_root.resolve():
        fail("PUBLISH_WRONG_DIRECTORY")
    if git_text("rev-parse", "--show-toplevel") != str(repo_root.resolve()):
        fail("PUBLISH_WRONG_REPOSITORY_ROOT")
    if not COMMIT_HASH.fullmatch(code_commit) or git_text("rev-parse", "HEAD") != code_commit:
        fail("PUBLISH_CODE_COMMIT_MISMATCH")
    if git("status", "--porcelain", "--untracked-files=all").stdout:
        fail("PUBLISH_WORKTREE_DIRTY")
    if strict_remote:
        remote = git_text("remote", "get-url", "origin")
        if remote not in (f"https://github.com/{REPO}", f"https://github.com/{REPO}.git"):
            fail("PUBLISH_REMOTE_INVALID")


def remote_head() -> str:
    # Fetch into FETCH_HEAD, never rebase/checkout remote code in the publisher.
    git("fetch", "--no-tags", "origin", "refs/heads/" + BRANCH)
    head = git_text("rev-parse", "FETCH_HEAD")
    if not COMMIT_HASH.fullmatch(head):
        fail("PUBLISH_REMOTE_HEAD_INVALID")
    return head


def remote_blob(commit: str, relative: str) -> bytes | None:
    exists = git("cat-file", "-e", f"{commit}:{relative}", allow_failure=True)
    if exists.returncode:
        return None
    data = git("show", f"{commit}:{relative}").stdout
    if len(data) > MAX_CSV:
        fail("PUBLISH_REMOTE_BLOB_TOO_LARGE")
    return data


def safe_target(repo_root: Path, name: str, corpus_root: str) -> tuple[str, Path]:
    if corpus_root != CORPUS_ROOT:
        fail("PUBLISH_ROOT_INVALID")
    d = file_date(name)
    relative = f"{CORPUS_ROOT}/{d.year}/{name}"
    target = repo_root / relative
    cursor = repo_root
    for part in Path(relative).parts:
        cursor /= part
        if cursor.is_symlink():
            fail("PUBLISH_PATH_SYMLINK")
    if target.resolve().is_relative_to((repo_root / CORPUS_ROOT).resolve()) is False:
        fail("PUBLISH_PATH_ESCAPE")
    return relative, target


def confirm_remote(expected_commit: str, relative: str, data: bytes) -> str:
    head = remote_head()
    content = remote_blob(head, relative)
    if content != data:
        fail("OUTCOME_UNKNOWN")
    if not git("merge-base", "--is-ancestor", expected_commit, head, allow_failure=True).returncode:
        return "CREATED"
    return "NOOP_ALREADY_PUBLISHED"


def publish_immutably(name: str, data: bytes, code_commit: str,
                        repo_root: Path, corpus_root: str = CORPUS_ROOT,
                        strict_remote: bool = True) -> str:
    assert_git_context(repo_root, code_commit, strict_remote)
    validate_csv_bytes(data)
    relative, target = safe_target(repo_root, name, corpus_root)
    head = remote_head()
    already = remote_blob(head, relative)
    if already is not None:
        if already == data:
            print(f"NOOP_ALREADY_PUBLISHED path={relative}")
            return "NOOP_ALREADY_PUBLISHED"
        fail("SAME_DAY_CONFLICT")
    if head != code_commit:
        fail("POLICY_GENERATION_CHANGED")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as f:
        f.write(data)
    git("add", "--", relative)
    changed = git("diff", "--cached", "--name-status", "--no-renames").stdout.decode("utf-8")
    if changed != f"A\t{relative}\n":
        fail("PUBLISH_UNEXPECTED_STAGED_PATH")
    if git("show", f":{relative}").stdout != data:
        fail("PUBLISH_STAGED_BYTES_MISMATCH")
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    git("commit", "-m", f"data(cbr): capture offices {file_date(name).isoformat()}")
    our_commit = git_text("rev-parse", "HEAD")
    diff = git("diff-tree", "--no-commit-id", "--name-status", "-r", our_commit).stdout.decode("utf-8")
    if diff != f"A\t{relative}\n":
        fail("PUBLISH_COMMIT_PATH_INVALID")
    pushed = git("push", "origin", "HEAD:refs/heads/" + BRANCH, allow_failure=True)
    try:
        outcome = confirm_remote(our_commit, relative, data)
    except CaptureError:
        fail("OUTCOME_UNKNOWN")
    if outcome == "CREATED":
        print(f"CREATED path={relative} commit={our_commit}")
        return outcome
    if pushed.returncode:
        # Another writer won the race; any same-byte remote result is a NOOP.
        print(f"NOOP_ALREADY_PUBLISHED path={relative}")
        return outcome
    fail("OUTCOME_UNKNOWN")


def verify_environment() -> str:
    if (os.getenv("GITHUB_REPOSITORY") != REPO or os.getenv("EXPECTED_REPOSITORY") != REPO
            or os.getenv("GITHUB_REF") != "refs/heads/" + BRANCH
            or os.getenv("GITHUB_EVENT_NAME") not in ("schedule", "workflow_dispatch")
            or os.getenv("GITHUB_EVENT_REPOSITORY_PRIVATE", "false") != "false"):
        fail("PUBLISH_CONTEXT_NOT_ALLOWED")
    sha = os.getenv("GITHUB_SHA", "")
    if sha != os.getenv("EXPECTED_CODE_COMMIT") or not COMMIT_HASH.fullmatch(sha):
        fail("PUBLISH_EVENT_SHA_MISMATCH")
    return sha


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest="command", required=True)
    cap = commands.add_parser("capture")
    cap.add_argument("--output-dir", type=Path, required=True)
    cap.add_argument("--github-output", type=Path)
    val = commands.add_parser("validate")
    val.add_argument("--file", type=Path, required=True)
    pub = commands.add_parser("publish")
    pub.add_argument("--input-dir", type=Path, required=True)
    pub.add_argument("--corpus-root", default=CORPUS_ROOT)
    args = p.parse_args()
    try:
        if args.command == "capture":
            capture(args.output_dir, args.github_output)
        elif args.command == "validate":
            _, obs = validate_csv_bytes(args.file.read_bytes())
            print(f"VALID observations={obs}")
        elif args.command == "publish":
            code_commit = verify_environment()
            name, data = validate_artifact(args.input_dir, os.getenv("EXPECTED_CSV_SHA256", ""))
            publish_immutably(name, data, code_commit, Path.cwd(), args.corpus_root)
    except (CaptureError, OSError, subprocess.TimeoutExpired) as exc:
        # Never log source HTML, bank names, executable input or token material.
        code = str(exc) if isinstance(exc, CaptureError) else "LOCAL_IO_OR_TIMEOUT"
        print(f"ERROR {code}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
