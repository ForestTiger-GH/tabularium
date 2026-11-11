#!/usr/bin/env python3
"""One-time, fail-closed FNS 1-YUR field-only semantic migration.

Never normalize a number, add missing values, reorder a geographic row, or
synthesize a legacy category. Store exact per-release source-column lineage
in one immutable manifest; the original CSV remains accessible through Git
history. Modes: dry-run, migrate, verify.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import fns_1yur_semantics as semantic
from migrated_flake_paths import current_csv_path

CORPUS = ROOT / "flakes/organizations/legal-entity-population"
EVENTS = ROOT / "_mw/work/publication-monitor/fns_1yur_events.jsonl"
MANIFEST = CORPUS / "field-provenance.json"
MANIFEST_VERSION = "fns-1yur-canonical-migration-1"
EXPECTED_TOTAL = 178
EXPECTED_BY_EPOCH = {"A": 16, "B": 69, "C1": 23, "C2": 24, "C3": 46}
# Source date coverage is checked by a deliberately narrow list of allowable
# final years; no missing July 2015 file is fabricated.
SOURCE_MISSING_2015 = date(2015, 7, 1)


class MigrationError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode_json(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def latest_event_hashes():
    if not EVENTS.is_file():
        raise MigrationError("PUBLICATION_EVENT_LOG_MISSING")
    latest = {}
    source_events = {}
    for line in EVENTS.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        item = json.loads(line)
        d = item.get("reference_date")
        if (d and item.get("csv_sha256") and item["type"] in
            ("PUBLISHED_NEW", "PUBLISHED_UPDATED",
             "BASELINE_IMPORTED", "BASELINE_CORRECTED",
             "SCHEMA_MIGRATED")):
            latest[d] = item["csv_sha256"]
            source_events.setdefault(d, []).append(item)
    return latest, source_events


def files_for_migration():
    paths = sorted(CORPUS.glob("*/*_1-YUR.csv"))
    if len(paths) != EXPECTED_TOTAL:
        raise MigrationError("UNEXPECTED_SOURCE_FILE_COUNT:" + str(len(paths)))
    dates = []
    for path in paths:
        day = date.fromisoformat(path.name[:10])
        if path.name != day.isoformat() + "_1-YUR.csv" or path.parent.name != str(day.year):
            raise MigrationError("INVALID_SOURCE_DATE_PATH:" + str(path))
        dates.append(day)
    if len(set(dates)) != EXPECTED_TOTAL or SOURCE_MISSING_2015 in dates:
        raise MigrationError("DATE_COVERAGE_INVALID")
    if dates[0] != date(2012, 1, 1) or dates[-1] != date(2026, 11, 1):
        raise MigrationError("SCOPE_BOUNDARIES_CHANGED")
    return paths


def check_identity_sums(data):
    """Check reported source hierarchy, not an analytical assumption."""
    import csv
    import io
    record = csv.DictReader(io.StringIO(data.decode("utf-8"), newline=""))
    columns = set(record.fieldnames or [])
    tested = 0
    for line in record:
        for construct in semantic.MEASURE_ORDER:
            names = ["le_" + construct + "__" + name for name in
                     ("all", "commercial", "nonprofit")]
            if set(names).issubset(columns):
                if int(line[names[0]]) != int(line[names[1]]) + int(line[names[2]]):
                    raise MigrationError("SOURCE_CLASS_SUBTOTAL_CONFLICT:" + str(names))
                tested += 1
    return tested


def make_candidate():
    latest, sources = latest_event_hashes()
    paths = files_for_migration()
    epochs = Counter()
    converted = []
    index = []
    check_count = 0
    retained_total = 0
    omitted_total = 0
    for path in paths:
        day = date.fromisoformat(path.name[:10])
        name = day.isoformat()
        original = path.read_bytes()
        raw_hash = digest(original)
        if latest.get(name) != raw_hash:
            raise MigrationError("SOURCE_EVENT_HASH_MISMATCH:" + name)
        output, provenance = semantic.convert(day, original)
        if raw_hash == digest(output):
            raise MigrationError("CANONICALIZATION_NOT_APPLIED:" + name)
        before = semantic._read_csv(original)
        after = semantic._read_csv(output)
        if len(before) != len(after):
            raise MigrationError("GEOGRAPHY_ROW_COUNT_CHANGED:" + name)
        for line_before, line_after in zip(before[1:], after[1:]):
            if line_before[:2] != line_after[:2]:
                raise MigrationError("GEOGRAPHY_ROW_CHANGED:" + name)
        if semantic.epoch(day) == "C3":
            if any(x["reason"] == "omitted_no_reported_modern_equivalent"
                   for x in provenance["omitted_fields"]):
                raise MigrationError("MODERN_SOURCE_MEASURE_DROPPED:" + name)
        if name == "2019-06-01" and (
            provenance["canonical_columns"] != 4 or
            {x["canonical_field"] for x in provenance["retained_fields"]} !=
            {"le_not_ceased__all", "le_ceased_bankruptcy_liquidation__all"}):
            raise MigrationError("HISTORICAL_2019_SOURCE_SUBSET_CHANGED")
        epochs[provenance["epoch"]] += 1
        check_count += check_identity_sums(output)
        retained_total += len(provenance["retained_fields"])
        omitted_total += len(provenance["omitted_fields"])
        converted.append((path, output))
        index.append({
            "reference_date": name,
            "path": path.relative_to(ROOT).as_posix(),
            "source_csv_sha256": raw_hash,
            "canonical_csv_sha256": provenance["canonical_csv_sha256"],
            "source_geographic_rows": provenance["rows"],
            "source_columns": provenance["source_columns"],
            "canonical_columns": provenance["canonical_columns"],
            "taxonomy_epoch": provenance["epoch"],
            "source_fields_retained": provenance["retained_fields"],
            "source_fields_omitted": provenance["omitted_fields"],
        })
    if dict(epochs) != EXPECTED_BY_EPOCH:
        raise MigrationError("TAXONOMY_PERIOD_COUNTS_DIFFER:" + str(dict(epochs)))
    if check_count != 40506:
        raise MigrationError("EXPECTED_SOURCE_ARITHMETIC_CHECKS_DIFFER:" + str(check_count))
    observed_dates = {e["reference_date"] for e in index}
    if set(latest) != observed_dates:
        raise MigrationError("EVENT_DATE_COVERAGE_CHANGED")
    manifest = {
        "version": MANIFEST_VERSION,
        "semantic_map_version": semantic.MAP_VERSION,
        "scope": "reported FNS 1-YUR columns, preserving source values",
        "status": "reported-only-rename-or-omit; no arithmetic derivations",
        "original_source_csv_recoverable_from": "Git commit parent of the migration",
        "reference_dates": len(index),
        "source_value_checks": check_count,
        "total_retained_source_fields": retained_total,
        "total_excluded_source_fields": omitted_total,
        "epoch_counts": dict(sorted(epochs.items())),
        "mapping": index,
    }
    body = encode_json(manifest)
    info = {
        "reference_dates": len(index),
        "epoch_counts": dict(sorted(epochs.items())),
        "source_hierarchy_checks": check_count,
        "retained_columns_by_date_total": retained_total,
        "excluded_columns_by_date_total": omitted_total,
        "new_manifest_sha256": digest(body),
        "manifest_bytes": len(body),
        "date_examples": [
            {k:entry[k] for k in ("reference_date", "source_columns",
                                   "canonical_columns", "taxonomy_epoch")}
            for entry in index if entry["reference_date"] in
            ("2012-01-01","2013-04-01","2013-05-01","2019-02-01",
             "2019-03-01","2019-06-01","2021-02-01","2023-02-01","2026-11-01")
        ],
    }
    return converted, body, info, index


def migrate():
    if MANIFEST.exists():
        raise MigrationError("MIGRATION_MANIFEST_ALREADY_EXISTS")
    converted, body, info, index = make_candidate()
    print("FNS_CANONICAL_PRECOMMIT_AUDIT_OK",json.dumps(info,ensure_ascii=False),flush=True)
    # Prepare candidate bytes before touching any source path. The one Git
    # commit, not filesystem writes, is the publication transaction boundary.
    with tempfile.TemporaryDirectory(prefix="fns-1yur-canonical-") as folder:
        tmp = Path(folder)
        for i, (path, data) in enumerate(converted):
            (tmp / str(i)).write_bytes(data)
        (tmp / "field-provenance.json").write_bytes(body)
        for i, (path, _data) in enumerate(converted):
            os.replace(tmp / str(i), path)
        os.replace(tmp / "field-provenance.json", MANIFEST)
    moment = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
    with EVENTS.open("a",encoding="utf-8",newline="\n") as out:
        for item in index:
            ident = "fns-1yur-schema-" + item["reference_date"] + "-" + item["canonical_csv_sha256"][:16]
            event = {
                "type":"SCHEMA_MIGRATED",
                "event_id":ident,
                "reference_date":item["reference_date"],
                "csv_path":item["path"],
                "prior_csv_sha256":item["source_csv_sha256"],
                "csv_sha256":item["canonical_csv_sha256"],
                "map_version":semantic.MAP_VERSION,
                "manifest_sha256":digest(body),
                "transformation":"reported column identity only; remove unmatched historic columns",
                "values_calculated":False,
                "notified":False,
                "observed_at":moment,
            }
            out.write(json.dumps(event,ensure_ascii=False,sort_keys=True,
                                 separators=(",",":"))+"\n")
    verify()
    print("FNS_CANONICAL_MIGRATION_READY_TO_COMMIT",len(converted),flush=True)


def verify():
    """Check the immutable 178-release mapping without rejecting later revisions.

    The original canonical SHA belongs to a historical snapshot. A different
    current CSV must match a later publication event under the new flake path.
    """
    if not MANIFEST.is_file():
        raise MigrationError("CANONICAL_MANIFEST_NOT_FOUND")
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if doc.get("version") != MANIFEST_VERSION:
        raise MigrationError("UNKNOWN_CANONICAL_MANIFEST")
    if len(doc["mapping"]) != EXPECTED_TOTAL:
        raise MigrationError("CANONICAL_MANIFEST_FILE_COUNT_BAD")
    latest, events_by_date = latest_event_hashes()
    unchanged_checks = 0
    revised = 0
    for item in doc["mapping"]:
        d = date.fromisoformat(item["reference_date"])
        # The manifest's original scrolls path is a historical fact.
        path = ROOT / current_csv_path(item["path"])
        content = path.read_bytes()
        current_hash = digest(content)
        if latest.get(d.isoformat()) != current_hash:
            raise MigrationError("CANONICAL_EVENT_HASH_MISMATCH:" + d.isoformat())
        fields, rows = semantic.validate_canonical(content)
        checks = check_identity_sums(content)
        if current_hash == item["canonical_csv_sha256"]:
            if len(rows) != item["source_geographic_rows"]:
                raise MigrationError("CANONICAL_GEO_ROW_COUNT_MISMATCH:" + d.isoformat())
            if len(fields) != item["canonical_columns"]:
                raise MigrationError("CANONICAL_FIELD_COUNT_MISMATCH:" + d.isoformat())
            unchanged_checks += checks
        else:
            # Only a new, explicit, already published revision permits a
            # deviation from the historical canonical snapshot.
            if not any(e.get("type") in ("PUBLISHED_NEW", "PUBLISHED_UPDATED")
                       and e.get("csv_sha256") == current_hash
                       and e.get("csv_path") == current_csv_path(item["path"])
                       for e in events_by_date.get(d.isoformat(), [])):
                raise MigrationError("UNTRACEABLE_CURRENT_REVISION:" + d.isoformat())
            revised += 1
    if revised == 0 and unchanged_checks != 40506:
        raise MigrationError("CANONICAL_IDENTITY_SUMS_MISMATCH")
    print("FNS_CANONICAL_POSTCOMMIT_VERIFY_OK",
          json.dumps({"historical_dates": EXPECTED_TOTAL,
                      "unchanged_snapshot_dates": EXPECTED_TOTAL - revised,
                      "event_backed_revisions": revised,
                      "unchanged_snapshot_identity_checks": unchanged_checks},
                     ensure_ascii=False), flush=True)
    return 0


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("dry-run","migrate","verify"))
    args = p.parse_args(argv)
    try:
        if args.mode == "verify":
            return verify()
        if args.mode == "dry-run":
            _,_,info,_ = make_candidate()
            print("FNS_CANONICAL_DRY_RUN_OK",json.dumps(info,ensure_ascii=False),flush=True)
            return 0
        return migrate()
    except (MigrationError,semantic.SchemaError,OSError,ValueError,KeyError) as exc:
        print("::error::FNS_CANONICAL_MIGRATION_BLOCKED",str(exc),flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
