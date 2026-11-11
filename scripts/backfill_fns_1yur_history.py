#!/usr/bin/env python3
"""Import official Form 1-YUR historical snapshots from 2012 without fabricating values.

Each accepted date is its own wide regional CSV. History is imported silently
with full source provenance; regular scheduled new releases still notify.
"""
from __future__ import annotations
import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "_mw/work/publication-monitor"))
import capture_fns_1yur_history as history
import capture_fns_1yur as modern
import fns_1yur_pipeline as service


def operate(start, end, *, max_releases=0, dry_run=False):
    if not history.MIN_DATE <= start <= end <= date.today():
        raise history.HistoryError("HISTORY_PERIOD_INVALID")
    if max_releases < 0:
        raise history.HistoryError("HISTORY_MAX_NEGATIVE")
    _, published, acked = service.events_read()
    releases, failed_pages = history.discover(start, end)
    selected = sorted(releases)
    if max_releases:
        selected = selected[:max_releases]
    staged, errors, existing, done = [], [], [], []
    for day in selected:
        target = service.REPO / modern.file_for(day)
        if target.exists():
            existing.append(day.isoformat())
            continue
        page, source_url = releases[day]
        try:
            data, meta = history.capture(day, page, source_url)
            fields, observed_rows = modern.read_csv(data)
            if len(observed_rows) != meta["rows"]:
                raise history.HistoryError("CSV_SOURCE_ROW_COUNT_MISMATCH")
            if not data.startswith(b"region_code,region_name,"):
                raise history.HistoryError("CSV_HEADER_INVALID")
            if dry_run:
                print("HISTORY_DRY", day, meta["source_indicator_map"],
                      meta["regions"], meta["legal_kinds"], flush=True)
                done.append(day.isoformat())
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            event = service.event_for(day, "NEW", data, meta["regions"], meta)
            event["type"] = "BASELINE_IMPORTED"
            event["backfill"] = True
            event["source_indicator_map"] = meta["source_indicator_map"]
            event["source_kind_codes"] = meta["kind_codes"]
            event["source_container_format"] = meta["container_format"]
            event["source_cells_crosschecked"] = meta["crosschecked_values"]
            event["federal_districts"] = meta["federal_districts"]
            event["source_geographic_rows"] = meta["rows"]
            event["source_kind_metric_coverage"] = meta["source_kind_metric_coverage"]
            event["overlapping_territory_codes"] = meta["overlapping_territory_codes"]
            event["national_territorial_differences"] = meta["national_territorial_differences"]
            event["source_orientation_disagreements"] = meta["orientation_disagreements"]
            event["source_orientation_disagreements_count"] = meta["orientation_disagreements_count"]
            event["source_orientation_disagreements_sha256"] = meta["orientation_disagreements_sha256"]
            event["source_kind_labels"] = meta["kind_labels"]
            service.append_events([event])
            staged.append((day, service.relative(target)))
            print("HISTORY_STAGED", day, "regions", meta["regions"],
                  "kinds", meta["legal_kinds"], "mapping", meta["source_indicator_map"],
                  flush=True)
            if len(staged) == 8:
                service.safe_publish([path for _, path in staged] +
                    [service.relative(service.EVENTS)],
                    "data(fns): backfill 8 source-verified 1-YUR historical dates")
                done.extend(x.isoformat() for x, _ in staged)
                print("HISTORY_PUSHED", [str(x) for x, _ in staged], flush=True)
                staged.clear()
        except (history.HistoryError, modern.SourceError, ValueError, OSError) as exc:
            errors.append((day.isoformat(), str(exc)))
            print("::warning::FNS_HISTORY_BLOCKED", day, str(exc), flush=True)
    if staged and not dry_run:
        service.safe_publish([path for _, path in staged] +
            [service.relative(service.EVENTS)],
            "data(fns): backfill " + str(len(staged)) + " source-verified 1-YUR dates")
        done.extend(x.isoformat() for x, _ in staged)
        print("HISTORY_PUSHED", [str(x) for x, _ in staged], flush=True)
    info = {"discovered": len(selected), "published_or_validated": len(done),
            "already_existing": len(existing), "blocked": errors,
            "year_discovery_errors": failed_pages, "dry_run": dry_run}
    print("FNS_1YUR_HISTORY_COMPLETE", json.dumps(info, ensure_ascii=False), flush=True)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as out:
            out.write("### FNS 1-YUR history 2012+\n\n")
            out.write("Discovered %s; published or validated %s; existing %s; blocked %s.\n\n" %
                      (len(selected), len(done), len(existing), len(errors)))
            for day, reason in errors:
                out.write("- " + day + " : " + reason.replace("\n", " ") + "\n")
    return 1 if errors or failed_pages else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-date", default="2012-01-01")
    parser.add_argument("--to-date", default="2026-11-01")
    parser.add_argument("--max-releases", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        return operate(date.fromisoformat(args.from_date), date.fromisoformat(args.to_date),
                       max_releases=args.max_releases, dry_run=args.dry_run)
    except (history.HistoryError, modern.SourceError, service.PipelineError,
            OSError, ValueError) as exc:
        print("::error::FNS_1YUR_HISTORY_FAILED", str(exc), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
