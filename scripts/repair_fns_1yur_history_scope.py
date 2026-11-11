#!/usr/bin/env python3
"""Remove non-entity registration-record measures from imported FNS 1-YUR CSVs.

Uses the verbatim national-sheet kind labels already attached to each original
BASELINE_IMPORTED event. All retained values, row order, and missing-measure
coverage stay unchanged. Append a traceable correction event; do not rewrite
the original provenance. Safe to rerun: an already corrected snapshot is skipped.
"""
from __future__ import annotations
import argparse
import csv
from datetime import date, datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "_mw/work/publication-monitor"))

import capture_fns_1yur as source
import capture_fns_1yur_history as history
import fns_1yur_pipeline as service


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def prune_csv(data, remove_codes):
    """Delete columns only, preserving every printed row and retained value."""
    raw = list(csv.reader(io.StringIO(data.decode("utf-8"), newline="")))
    if not raw or len(raw) < 60:
        raise history.HistoryError("CORRECTION_CSV_EMPTY")
    header = raw[0]
    remove = [
        name for name in header[2:] if
        (re.fullmatch(r"c\d{2}_(\d{4})", name) is not None and
         name.rsplit("_", 1)[1] in remove_codes)
    ]
    if not remove:
        raise history.HistoryError("NON_ENTITY_COLUMNS_NOT_FOUND")
    if any(not name.startswith("c01_") for name in remove):
        # Other indicators would signify a different source layout requiring
        # source-specific review rather than automated deletion.
        raise history.HistoryError("NON_ENTITY_SHEET_HAS_EXTRA_MEASURES")
    retained = [i for i, name in enumerate(header) if name not in remove]
    if len({h.rsplit("_", 1)[1] for h in header[2:] if h.startswith("c01_")}) <= len(remove_codes):
        raise history.HistoryError("WOULD_REMOVE_ALL_LEGAL_KINDS")
    for record in raw[1:]:
        if len(record) != len(header):
            raise history.HistoryError("SOURCE_CSV_ROW_WIDTH_MISMATCH")
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow([header[i] for i in retained])
    for record in raw[1:]:
        writer.writerow([record[i] for i in retained])
    new = output.getvalue().encode("utf-8")
    original_head, original_rows = source.read_csv(data)
    new_head, new_rows = source.read_csv(new)
    if list(original_rows) != list(new_rows) or len(original_rows) != len(new_rows):
        raise history.HistoryError("CORRECTION_ROW_OR_ORDER_CHANGED")
    if [x for x in original_head if x not in remove] != new_head:
        raise history.HistoryError("CORRECTION_COLUMNS_CHANGED")
    for key, old_values in original_rows.items():
        old_record = dict(zip(original_head, old_values))
        new_record = dict(zip(new_head, new_rows[key]))
        if any(old_record[name] != new_record[name] for name in new_head):
            raise history.HistoryError("CORRECTION_RETAINED_VALUE_CHANGED")
    return new, remove, len(original_rows)


def read_baselines_and_corrections():
    service.events_read()  # Validate established event contract, including corrections.
    baselines, corrections = {}, {}
    for line in service.EVENTS.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        event = json.loads(line)
        if event["type"] == "BASELINE_IMPORTED":
            key = event["reference_date"]
            if key in baselines:
                raise history.HistoryError("HISTORY_DUPLICATE_BASELINE_DATE")
            baselines[key] = event
        elif event["type"] == "BASELINE_CORRECTED":
            corrections[event["reference_date"]] = event
    return baselines, corrections


def repair(dry_run=False):
    baselines, corrections = read_baselines_and_corrections()
    candidates = []
    excluded_summary = {}
    for day, event in sorted(baselines.items()):
        labels = event.get("source_kind_labels")
        if not isinstance(labels, dict):
            raise history.HistoryError("HISTORY_BASELINE_MISSING_SOURCE_KIND_LABELS:" + day)
        excluded = {
            code: label for code, label in labels.items()
            if history.is_registration_record_label(label)
        }
        if not excluded:
            continue
        excluded_summary[day] = excluded
        if len(excluded) > 3:
            raise history.HistoryError("HISTORY_UNEXPECTED_REGISTRATION_RECORD_CLASSES:" + day)
        d = date.fromisoformat(day)
        target = service.REPO / source.file_for(d)
        if not target.is_file() or event.get("csv_path") != service.relative(target):
            raise history.HistoryError("HISTORY_MISSING_OR_UNEXPECTED_SOURCE_CSV:" + day)
        original = target.read_bytes()
        current_sha = sha256(original)
        previous = corrections.get(day)
        if previous is not None:
            if (previous.get("csv_sha256") != current_sha or
                    set(previous.get("removed_source_kind_codes", [])) != set(excluded)):
                raise history.HistoryError("HISTORY_PREVIOUS_CORRECTION_MISMATCH:" + day)
            continue
        if current_sha != event["csv_sha256"]:
            raise history.HistoryError("HISTORY_FILE_MODIFIED_SINCE_IMPORT:" + day)
        new, removed_columns, row_count = prune_csv(original, set(excluded))
        if current_sha == sha256(new):
            raise history.HistoryError("CORRECTION_NEW_DIGEST_UNCHANGED:" + day)
        correction = {
            "type": "BASELINE_CORRECTED",
            "event_id": "fns-1yur-scope-" + day + "-" + sha256(new)[:18],
            "baseline_event_id": event["event_id"],
            "reference_date": day,
            "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "csv_path": service.relative(target),
            "prior_csv_sha256": current_sha,
            "csv_sha256": sha256(new),
            "removed_source_kind_codes": sorted(excluded),
            "removed_source_kind_labels": excluded,
            "removed_columns": removed_columns,
            "retained_rows": row_count,
            "scope_reason": "FNS national summary identifies these worksheets as registration RECORDS, not legal entities",
        }
        candidates.append((target, new, correction))
    print("FNS_HISTORY_SCOPE_AUDIT", json.dumps({
        "baseline_events": len(baselines),
        "affected_dates": len(excluded_summary),
        "already_corrected": sum(day in corrections for day in excluded_summary),
        "new_corrections": len(candidates),
        "source_non_entity_codes": sorted(set(
            code for sub in excluded_summary.values() for code in sub)),
        "dry_run": dry_run,
    }, ensure_ascii=False), flush=True)
    if dry_run:
        for target, _, event in candidates[:12]:
            print("FNS_HISTORY_SCOPE_CANDIDATE", event["reference_date"],
                  event["removed_columns"], flush=True)
        return 0
    batch = []
    for target, data, event in candidates:
        target.write_bytes(data)
        service.append_events([event])
        batch.append(service.relative(target))
        if len(batch) == 10:
            service.safe_publish(batch + [service.relative(service.EVENTS)],
                                 "data(fns): remove registration-record columns from 1-YUR source representations")
            print("FNS_HISTORY_SCOPE_PUBLISHED", len(batch),
                  event["reference_date"], flush=True)
            batch.clear()
    if batch:
        service.safe_publish(batch + [service.relative(service.EVENTS)],
                             "data(fns): finish 1-YUR legal-entity scope corrections")
        print("FNS_HISTORY_SCOPE_PUBLISHED", len(batch), "final", flush=True)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    try:
        return repair(dry_run=args.dry_run)
    except (history.HistoryError, source.SourceError, service.PipelineError,
            OSError, ValueError, KeyError) as exc:
        print("::error::FNS_HISTORY_SCOPE_CORRECTION_FAILED", str(exc), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
