#!/usr/bin/env python3
"""Operational publication and Telegram outbox for FNS legal-entity 1-YUR releases."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
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
import capture_fns_1yur as source
from migrated_flake_paths import current_csv_path
from monitor import MonitorError, send_telegram

EVENTS = HERE / "fns_1yur_events.jsonl"
WATCHED_CODE = ("AGENTS.md", "scripts/capture_fns_1yur.py",
                "scripts/migrated_flake_paths.py",
                "flakes/organizations/legal-entity-population/README.md",
                "scripts/fns_1yur_semantics.py",
                "scripts/capture_fns_1yur_history.py",
                "scripts/backfill_fns_1yur_history.py",
                "scripts/requirements_fns_1yur.txt",
                "_mw/work/publication-monitor/fns_1yur_pipeline.py",
                ".github/workflows/publication-monitor.yml")
REPO_NAME = "ForestTiger-GH/tabularium"


class PipelineError(Exception):
    pass


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def relative(path):
    return Path(path).resolve().relative_to(REPO.resolve()).as_posix()


def git(*args, check=True):
    proc = subprocess.run(("git",) + args, cwd=REPO, text=True, capture_output=True)
    if check and proc.returncode != 0:
        raise PipelineError("GIT_FAILED:" + " ".join(args[:3]) + ":" + proc.stderr[-160:])
    return proc


def events_read(path=EVENTS):
    items, published, acked, baselined, corrected, migrated = [], {}, set(), set(), set(), set()
    if not Path(path).exists():
        return items, published, acked
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            raise PipelineError("OUTBOX_CORRUPT") from None
        if not isinstance(item, dict) or "type" not in item or "event_id" not in item:
            raise PipelineError("OUTBOX_SCHEMA_INVALID")
        ident = item["event_id"]
        if item["type"] in ("PUBLISHED_NEW", "PUBLISHED_UPDATED"):
            if ident in published:
                raise PipelineError("DUPLICATE_PUBLICATION_EVENT")
            published[ident] = item
        elif item["type"] == "BASELINE_IMPORTED":
            if ident in baselined or ident in published:
                raise PipelineError("DUPLICATE_HISTORICAL_BASELINE")
            baselined.add(ident)
        elif item["type"] == "BASELINE_CORRECTED":
            if ident in corrected or item.get("baseline_event_id") not in baselined:
                raise PipelineError("INVALID_HISTORICAL_CORRECTION")
            corrected.add(ident)
        elif item["type"] == "SCHEMA_MIGRATED":
            if ident in migrated:
                raise PipelineError("DUPLICATE_SCHEMA_MIGRATION_EVENT")
            migrated.add(ident)
        elif item["type"] == "NOTIFIED":
            if ident in acked:
                raise PipelineError("DUPLICATE_ACK")
            acked.add(ident)
        else:
            raise PipelineError("UNKNOWN_OUTBOX_EVENT")
        items.append(item)
    if not acked.issubset(published):
        raise PipelineError("ORPHAN_OUTBOX_ACK")
    return items, published, acked


def append_events(records, path=EVENTS):
    if not records:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("a", encoding="utf-8", newline="\n") as out:
        for item in records:
            out.write(json.dumps(item, ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":")) + "\n")


def safe_publish(paths, message):
    paths = sorted(set(paths))
    if not paths:
        return False
    base = git("rev-parse", "HEAD").stdout.strip()
    # Rebase replays the commit, so identity must also be configured for that
    # operation; -c only on git commit is insufficient.
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email",
        "41898282+github-actions[bot]@users.noreply.github.com")
    git("add", "--", *paths)
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        return False
    git("-c", "user.name=github-actions[bot]",
        "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "commit", "-m", message)
    for _ in range(3):
        git("fetch", "origin", "main")
        watched = paths + list(WATCHED_CODE)
        if git("diff", "--quiet", base, "origin/main", "--", *watched, check=False).returncode:
            raise PipelineError("CONCURRENT_INPUT_OR_OUTPUT_CHANGE")
        git("rebase", "origin/main")
        if git("push", "origin", "HEAD:main", check=False).returncode == 0:
            return True
    raise PipelineError("PUSH_REJECTED")


def event_for(d, status, data, changed, metadata):
    digest = hashlib.sha256(data).hexdigest()
    now = stamp()
    identity = hashlib.sha256((d.isoformat() + digest + now).encode()).hexdigest()[:20]
    return {
        "type": "PUBLISHED_" + status,
        "event_id": "fns-1yur-" + identity,
        "observed_at": now,
        "reference_date": d.isoformat(),
        "csv_path": source.file_for(d).as_posix(),
        "csv_sha256": digest,
        "source_page": metadata["source_page"],
        "archive_url": metadata["archive_url"],
        "archive_sha256": metadata["archive_sha256"],
        "member_name": metadata["member_name"],
        "member_sha256": metadata["member_sha256"],
        "regions": metadata["regions"],
        "legal_kinds": metadata["legal_kinds"],
        "federal_districts": metadata.get("federal_districts"),
        "source_geographic_rows": metadata.get("rows"),
        "source_kind_metric_coverage": metadata.get("source_kind_metric_coverage"),
        "source_indicator_map": metadata.get("source_indicator_map"),
        "overlapping_territory_codes": metadata.get("overlapping_territory_codes", {}),
        "national_territorial_differences": metadata.get("national_territorial_differences", []),
        "source_orientation_disagreements": metadata.get("orientation_disagreements", []),
        "source_orientation_disagreements_count": metadata.get("orientation_disagreements_count", 0),
        "source_orientation_disagreements_sha256": metadata.get("orientation_disagreements_sha256"),
        "source_kind_labels": metadata.get("kind_labels"),
        "semantic_map_version": metadata.get("semantic_map_version"),
        "raw_csv_sha256": metadata.get("raw_csv_sha256"),
        "canonical_retained_fields": metadata.get("canonical_retained_fields"),
        "canonical_omitted_fields": metadata.get("canonical_omitted_fields"),
        "excluded_source_non_entity_sheets": metadata.get("excluded_source_non_entity_sheets", {}),
        "excluded_incomplete_kind_sheets": metadata.get("excluded_incomplete_kind_sheets", {}),
        "source_sheet_order_disagreements": metadata.get("source_sheet_order_disagreements", []),
        "indicators": [v["source_indicator"] for v in
                       metadata.get("source_indicator_map", {}).values()] or ["1", "8", "12"],
        "changed_regions": changed,
        "parser_commit": git("rev-parse", "HEAD").stdout.strip(),
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
    }


def alert(event):
    d = date.fromisoformat(event["reference_date"])
    verb = "обновлён" if event["type"] == "PUBLISHED_UPDATED" else "добавлен"
    path = current_csv_path(event["csv_path"])
    url = "https://github.com/" + REPO_NAME + "/blob/main/" + path
    return (
        f"📊 <b>ФНС 1-ЮР: {verb} региональный срез</b>\n"
        f"Дата: {d:%d.%m.%Y}\n"
        f"Регионов: {event['regions']}; видов ЮЛ: {event['legal_kinds']}\n"
        f"Изменено регионов: {event['changed_regions']}\n"
        f"CSV SHA: <code>{event['csv_sha256'][:16]}</code>\n"
        f"<a href=\"{url}\">Файл в Tabularium</a>\n"
        f"Событие: <code>{event['event_id']}</code>"
    )


def flush_outbox():
    _, published, acked = events_read()
    pending = [item for key, item in published.items() if key not in acked]
    if not pending:
        return 0
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")
    thread = os.getenv("TELEGRAM_THREAD_ID")
    new = []
    for item in pending:
        if not token or not chat:
            print("::warning::FNS_1YUR_TELEGRAM_NOT_CONFIGURED")
            break
        try:
            send_telegram(token, chat, alert(item), thread)
            new.append({"type": "NOTIFIED", "event_id": item["event_id"],
                        "notified_at": stamp()})
        except MonitorError as exc:
            print("::warning::FNS_1YUR_NOTIFICATION_PENDING", item["event_id"], exc)
    if new:
        append_events(new)
        safe_publish([relative(EVENTS)], "chore(fns): acknowledge 1-YUR notifications")
    return len(pending) - len(new)


def choose_dates(available, mode, first=None, last=None):
    dates = sorted(available)
    if mode == "backfill":
        if not first or not last:
            raise PipelineError("BACKFILL_RANGE_REQUIRED")
        begin, end = date.fromisoformat(first), date.fromisoformat(last)
        if begin > end:
            raise PipelineError("BACKFILL_RANGE_REVERSED")
        selected = [d for d in dates if begin <= d <= end]
        if not 1 <= len(selected) <= 15:
            raise PipelineError("BACKFILL_LIMIT_15")
        return selected
    # Recheck the newest three source dates, and fill recent gaps in bounded batches.
    selected = set(dates[-3:])
    for d in dates[-9:]:
        if not (REPO / source.file_for(d)).exists():
            selected.add(d)
    return sorted(selected)[-9:]


def verify():
    files = sorted((REPO / source.CORPUS).glob("*/*_1-YUR.csv"))
    for file in files:
        try:
            d = date.fromisoformat(file.name[:10])
        except ValueError:
            raise PipelineError("INVALID_CORPUS_DATE") from None
        if relative(file) != source.file_for(d).as_posix():
            raise PipelineError("INVALID_CORPUS_PATH")
        source.read_csv(file.read_bytes())
    events_read()
    print("FNS_1YUR_VERIFY files=", len(files))
    return 0


def release_years(mode, first, last):
    if mode != "backfill":
        today = date.today()
        return [today.year - 1, today.year]
    begin, end = date.fromisoformat(first), date.fromisoformat(last)
    # January can appear on the previous reporting year's page.
    years = range(begin.year - 1, end.year + 1)
    return [year for year in years if year in source.PAGES or year >= 2027]


def process(mode, first=None, last=None):
    if mode in ("verify", "validate"):
        return verify()
    dry = mode == "dry-run"
    if not dry:
        flush_outbox()
    releases = source.discover(release_years(mode, first, last))
    selected = choose_dates(releases, mode, first, last)
    changed, failures = [], 0
    with tempfile.TemporaryDirectory(prefix="tabularium-fns-1yur-") as temp:
        for day in selected:
            try:
                source_page, archive_url = releases[day]
                data, meta = source.capture(day, archive_url)
                meta["source_page"] = source_page
                target = REPO / source.file_for(day)
                old = target.read_bytes() if target.exists() else None
                status, n = source.compare(old, data)
                print("FNS_1YUR_CHECK", day, status, "changed_regions=", n)
                if status != "NO_CHANGE":
                    stage = Path(temp) / source.file_for(day).name
                    stage.write_bytes(data)
                    changed.append((day, status, n, meta, stage))
            except (source.SourceError, OSError, ValueError) as exc:
                failures += 1
                print("::error::FNS_1YUR_CHECK_FAILED", day, exc)
        if dry:
            print("FNS_1YUR_DRY_RUN changed=", len(changed), "failures=", failures)
            return 1 if failures else 0
        if changed:
            paths, records = [], []
            for day, status, n, meta, stage in changed:
                target = REPO / source.file_for(day)
                target.parent.mkdir(parents=True, exist_ok=True)
                content = stage.read_bytes()
                target.write_bytes(content)
                paths.append(relative(target))
                records.append(event_for(day, status, content, n, meta))
            append_events(records)
            paths.append(relative(EVENTS))
            safe_publish(paths, "data(fns): publish " + str(len(changed)) + " 1-YUR regional snapshots")
    if not dry:
        flush_outbox()
    return 1 if failures else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("check", "dry-run", "verify", "validate", "backfill"))
    ap.add_argument("--from-date")
    ap.add_argument("--to-date")
    a = ap.parse_args(argv)
    try:
        return process(a.mode, a.from_date, a.to_date)
    except (source.SourceError, PipelineError, OSError, ValueError) as exc:
        print("::error::FNS_1YUR_PIPELINE_FAILED", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
