#!/usr/bin/env python3
"""Operational FNS pipeline: temporary capture, atomic corpus publication, JSONL outbox."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import capture_fns_sme as source
from monitor import send_telegram, MonitorError

EVENTS = HERE / "fns_sme_events.jsonl"
CHANGING_CODE = ("scripts/capture_fns_sme.py",
                 "_mw/work/publication-monitor/fns_sme_pipeline.py",
                 ".github/workflows/publication-monitor.yml")
REPO_NAME = "ForestTiger-GH/tabularium"


class PipelineError(Exception):
    pass


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def relative(path):
    return Path(path).resolve().relative_to(REPO.resolve()).as_posix()


def cmd(*args, check=True):
    r = subprocess.run(args, cwd=REPO, text=True, capture_output=True)
    if check and r.returncode:
        raise PipelineError(f"GIT_FAILED:{' '.join(args[:3])}:{r.stderr[-180:]}")
    return r


def events_read(path=None):
    path = EVENTS if path is None else Path(path)
    events, published, notified = [], {}, set()
    if not Path(path).exists():
        return events, published, notified
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            raise PipelineError("EVENT_LOG_CORRUPT") from None
        if not isinstance(event, dict) or "type" not in event:
            raise PipelineError("EVENT_LOG_SCHEMA_INVALID")
        if event["type"] in ("PUBLISHED_NEW", "PUBLISHED_UPDATED"):
            ident = event.get("event_id")
            if not isinstance(ident, str) or ident in published:
                raise PipelineError("DUPLICATE_EVENT_ID")
            published[ident] = event
        elif event["type"] == "NOTIFIED":
            ident = event.get("event_id")
            if not isinstance(ident, str) or ident in notified:
                raise PipelineError("DUPLICATE_NOTIFICATION")
            notified.add(ident)
        else:
            raise PipelineError("UNKNOWN_EVENT_TYPE")
        events.append(event)
    if not notified.issubset(published.keys()):
        raise PipelineError("ORPHAN_NOTIFICATION")
    return events, published, notified


def events_append(new_records, path=None):
    path = EVENTS if path is None else Path(path)
    if not new_records:
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fp:
        for event in new_records:
            fp.write(json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def make_event(d, status, data, source_sha, changed, *, now=None):
    stamp = now or utc_now()
    digest = hashlib.sha256(data).hexdigest()
    token = hashlib.sha256(f"{d.isoformat()}:{digest}:{stamp}".encode()).hexdigest()[:18]
    return {
        "type": f"PUBLISHED_{status}",
        "event_id": f"fns-sme-{token}",
        "observed_at": stamp,
        "reference_date": d.isoformat(),
        "csv_path": str(source.file_for(d).as_posix()),
        "csv_sha256": digest,
        "source_sha256": source_sha,
        "source_url": source.SOURCE_JSON,
        "request": {"method": "POST", "statDate": source.format_source_date(d)},
        "regions": len(source.read_csv(data)),
        "changed_regions": changed,
        "parser_commit": os.environ.get("GITHUB_SHA") or cmd("git", "rev-parse", "HEAD").stdout.strip(),
    }


def safe_publish(paths, message):
    paths = sorted(set(paths))
    if not paths:
        return False
    starting = cmd("git", "rev-parse", "HEAD").stdout.strip()
    cmd("git", "add", "--", *paths)
    if cmd("git", "diff", "--cached", "--quiet", check=False).returncode == 0:
        return False
    cmd("git", "-c", "user.name=github-actions[bot]",
        "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "commit", "-m", message)
    watched = paths + list(CHANGING_CODE)
    for attempt in range(3):
        cmd("git", "fetch", "origin", "main")
        if cmd("git", "diff", "--quiet", starting, "origin/main",
               "--", *watched, check=False).returncode != 0:
            raise PipelineError("CONCURRENT_CHANGE_TO_FNS_INPUT_OR_OUTPUT")
        cmd("git", "rebase", "origin/main")
        pushed = cmd("git", "push", "origin", "HEAD:main", check=False)
        if pushed.returncode == 0:
            return True
    raise PipelineError("PUSH_REJECTED")


def format_alert(event):
    update = event["type"] == "PUBLISHED_UPDATED"
    headline = "обновлён" if update else "добавлен"
    d = datetime.fromisoformat(event["reference_date"])
    url = f"https://github.com/{REPO_NAME}/blob/main/{event['csv_path']}"
    return (
        f"📊 <b>ФНС: {headline} региональный срез МСП</b>\n\n"
        f"Дата статистики: {d:%d.%m.%Y}\n"
        f"Регионов: {event['regions']}\n"
        f"Изменено регионов: {event['changed_regions']}\n"
        f"SHA CSV: <code>{event['csv_sha256'][:16]}</code>\n"
        f"Обнаружено: {event['observed_at']} (UTC)\n"
        f"<a href=\"{url}\">Файл в Tabularium</a>\n"
        f"Событие: <code>{event['event_id']}</code>")


def flush_outbox(*, dry_run=False):
    _, published, notified = events_read()
    pending = [e for key, e in published.items() if key not in notified]
    if dry_run:
        print(f"FNS_OUTBOX pending={len(pending)} (dry-run)")
        return len(pending)
    if not pending:
        return 0
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    thread = os.getenv("TELEGRAM_THREAD_ID")
    ack = []
    for event in pending:
        if not token or not chat:
            print("::warning::FNS_PENDING_NOTIFICATION TELEGRAM_NOT_CONFIGURED")
            break
        try:
            send_telegram(token, chat, format_alert(event), thread)
            ack.append({"type": "NOTIFIED", "event_id": event["event_id"],
                        "notified_at": utc_now()})
            print("FNS_NOTIFIED", event["event_id"])
        except MonitorError as e:
            print(f"::warning::FNS_PENDING_NOTIFICATION {event['event_id']} {e}")
    if ack:
        events_append(ack)
        safe_publish([relative(EVENTS)], f"chore(fns): acknowledge {len(ack)} SME notifications")
    return len(pending) - len(ack)


def select_dates(available, *, mode, from_date=None, to_date=None):
    if mode == "backfill":
        if not from_date or not to_date:
            raise PipelineError("BACKFILL_RANGE_REQUIRED")
        start, end = source.iso_to_date(from_date), source.iso_to_date(to_date)
        if start > end:
            raise PipelineError("BACKFILL_RANGE_REVERSED")
        selected = [d for d in available if start <= d <= end]
        if not 1 <= len(selected) <= 15:
            raise PipelineError("BACKFILL_BATCH_LIMIT_15")
        return selected
    if mode == "verify":
        return []
    # Latest two for detecting edits, plus missing dates from the latest eight.
    latest = set(available[-2:])
    for d in available[-8:]:
        if not source.file_for(d, REPO / source.CORPUS).exists():
            latest.add(d)
    return sorted(latest)


def verify():
    path = REPO / source.CORPUS
    files = sorted(path.glob("*/*_SME-REG.csv"))
    for file in files:
        match = source.NAME.fullmatch(file.name)
        if match is None:
            raise PipelineError("CORPUS_FILENAME_INVALID")
        d = source.iso_to_date(match[1])
        if relative(file) != source.file_for(d).as_posix():
            raise PipelineError("CORPUS_DATE_DIRECTORY_INVALID")
        source.read_csv(file.read_bytes())
    print(f"FNS_VERIFY files={len(files)}")
    return 0


def process(mode, *, from_date=None, to_date=None):
    if mode == "verify":
        return verify()
    if mode == "validate":
        events_read()
        return verify()
    no_write = mode == "dry-run"
    if not no_write:
        flush_outbox()
    dates = source.discover_dates()
    selected = select_dates(dates, mode=mode, from_date=from_date, to_date=to_date)
    updates = []
    problems = 0
    # Temporary technical layer: candidates never enter Git before validation.
    with tempfile.TemporaryDirectory(prefix="tabularium-fns-sme-") as staging:
        for d in selected:
            try:
                candidate, source_sha = source.capture(d)
                target = REPO / source.file_for(d)
                previous = target.read_bytes() if target.exists() else None
                status, count = source.compare(previous, candidate)
                print(f"FNS_CHECK {d.isoformat()} {status} changed_regions={count}")
                if status == "NO_CHANGE":
                    continue
                dest = Path(staging) / source.file_for(d).name
                dest.write_bytes(candidate)
                updates.append((d, status, count, source_sha, candidate, dest))
            except (source.FnsError, OSError) as exc:
                problems += 1
                print(f"::error::FNS_CHECK_FAILED {d.isoformat()} {exc}")
        if no_write:
            print(f"FNS_DRY_RUN changed={len(updates)} failed={problems}")
            return 1 if problems else 0
        if updates:
            paths = []
            journal = []
            for d, status, changed, digest, candidate, tmp in updates:
                target = REPO / source.file_for(d)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(tmp.read_bytes())
                paths.append(relative(target))
                journal.append(make_event(d, status, candidate, digest, changed))
            events_append(journal)
            paths.append(relative(EVENTS))
            safe_publish(paths, f"data(fns): publish {len(updates)} monthly SME regional snapshots")
            print(f"FNS_PUBLISHED count={len(updates)}")
    if not no_write:
        flush_outbox()
    return 1 if problems else 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("check", "dry-run", "backfill", "verify", "validate"))
    p.add_argument("--from-date")
    p.add_argument("--to-date")
    a = p.parse_args(argv)
    try:
        return process(a.mode, from_date=a.from_date, to_date=a.to_date)
    except (PipelineError, source.FnsError, OSError) as e:
        print("::error::FNS_PIPELINE_FAILED", e)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
