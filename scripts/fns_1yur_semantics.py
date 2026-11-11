#!/usr/bin/env python3
"""Canonical source-representation headings for FNS Form 1-YUR (2012 onward).

Column values are *only copied*, never calculated or filled. A historical
column with no approved contemporary construct match is deleted from the
canonical representation. The separate migration manifest is the reversible
source-column bridge; raw original CSVs remain in Git history.
"""
from __future__ import annotations

import csv
from datetime import date
import hashlib
import io
import re

MAP_VERSION = "fns-1yur-source-field-map-1"
FIRST = date(2012, 1, 1)
A_END = date(2013, 4, 1)
B_END = date(2019, 2, 1)
C1_END = date(2021, 1, 1)
C2_END = date(2023, 1, 1)

# The 2026 FNS taxonomy. All 37 headings are published source observations.
KINDS = {
    "1000": "all",
    "1100": "commercial",
    "1110": "general_partnership",
    "1120": "limited_partnership",
    "1130": "limited_liability_company_including_additional",
    "1131": "additional_liability_company",
    "1140": "joint_stock_company",
    "1141": "public_joint_stock_company",
    "1142": "nonpublic_joint_stock_company",
    "1143": "open_joint_stock_company",
    "1144": "closed_joint_stock_company",
    "1150": "production_cooperative",
    "1151": "agricultural_production_cooperative",
    "1160": "peasant_farm_enterprise",
    "1170": "unitary_enterprise",
    "1171": "federal_unitary_enterprise",
    "1172": "regional_unitary_enterprise",
    "1173": "municipal_unitary_enterprise",
    "1174": "federal_treasury_enterprise",
    "1175": "regional_treasury_enterprise",
    "1176": "municipal_treasury_enterprise",
    "1180": "other_commercial",
    "1190": "special_registration_commercial_cbr",
    "1200": "nonprofit",
    "1210": "consumer_cooperative",
    "1220": "real_estate_owners_association",
    "1221": "gardening_nonprofit_association",
    "1222": "homeowners_association",
    "1230": "institution",
    "1231": "federal_institution",
    "1232": "regional_institution",
    "1233": "municipal_institution",
    "1240": "special_registration_nonprofit",
    "1241": "special_registration_nonprofit_justice_ministry",
    "1242": "special_registration_nonprofit_cbr",
    "1250": "other_nonprofit",
    "1251": "personal_foundation",
}
assert len(KINDS) == 37 and len(set(KINDS.values())) == 37

# Explicit *published-kind* aliases. No arithmetic is allowed in these CSVs.
# A: through April 2013. B: May 2013 through February 2019.
# Reused codes like A:1030 and B:1030 must NEVER be aligned by code alone.
A = {
    "1010": "1000", "1020": "1100",
    "1021": "1110", "1022": "1120",
    "1023": "1130",   # FNS directly reports LLC together with additional-liability companies
    "1024": "1140", "1025": "1150", "1026": "1170",
    "1030": "1200", "1031": "1210", "1032": "1230",
}
B = {
    "1010": "1000", "1020": "1100",
    "1021": "1110", "1022": "1120",
    # 1023 is LLC *excluding* additional-liability companies: not the modern 1130.
    # B 1023 + B 1024 would be a DERIVATION, excluded from the source CSV.
    "1024": "1131",
    "1025": "1140", "1026": "1144", "1027": "1143",
    "1028": "1150", "1029": "1170",
    "1040": "1200", "1041": "1210", "1042": "1230",
    "1043": "1241",  # FNS reports MinJust special-registered entities within NPO
}
C = {code: code for code in KINDS}
SOURCE_PATTERN = re.compile(r"c([0-9]{2})_([0-9]{4})\Z")
FIELD_PATTERN = re.compile(r"le_(not_ceased|bankruptcy_proceedings|ceased_bankruptcy_liquidation)__([a-z][a-z0-9_]*)\Z")
GEO = re.compile(r"[0-9]{2}\Z")
PREFIXES = {
    "A": {"c01": "not_ceased", "c11": "ceased_bankruptcy_liquidation"},
    "B": {"c01": "not_ceased", "c11": "ceased_bankruptcy_liquidation"},
    "C1": {"c01": "not_ceased", "c12": "ceased_bankruptcy_liquidation"},
    "C2": {"c01": "not_ceased", "c09": "bankruptcy_proceedings",
           "c13": "ceased_bankruptcy_liquidation"},
    "C3": {"c01": "not_ceased", "c08": "bankruptcy_proceedings",
           "c12": "ceased_bankruptcy_liquidation"},
}
CATEGORY = {"A": A, "B": B, "C1": C, "C2": C, "C3": C}
MEASURE_ORDER = ("not_ceased", "bankruptcy_proceedings",
                 "ceased_bankruptcy_liquidation")
KIND_ORDER = list(KINDS)

class SchemaError(ValueError):
    """Unreviewed source layout, ambiguous mapping, or non-faithful conversion."""

def epoch(d):
    if isinstance(d, str):
        d = date.fromisoformat(d)
    if d < FIRST:
        raise SchemaError("DATE_BEFORE_REVIEWED_HISTORY")
    if d <= A_END: return "A"
    if d <= B_END: return "B"
    if d <= C1_END: return "C1"
    if d <= C2_END: return "C2"
    return "C3"

def mapping(d, original_column):
    """Return (canonical_column, disposition). Never invent a source field."""
    e = epoch(d)
    m = SOURCE_PATTERN.fullmatch(original_column)
    if m is None:
        raise SchemaError("UNEXPECTED_SOURCE_COLUMN:" + original_column)
    indicator, kind = ("c" + m.group(1)), m.group(2)
    construct = PREFIXES[e].get(indicator)
    if construct is None:
        raise SchemaError("UNREVIEWED_SOURCE_INDICATOR:" + original_column)
    aligned_kind = CATEGORY[e].get(kind)
    if aligned_kind is None:
        return None, "omitted_no_reported_modern_equivalent"
    target = "le_" + construct + "__" + KINDS[aligned_kind]
    return target, "reported_value_alias"

def _read_csv(contents):
    try:
        text = contents.decode("utf-8-sig")
        lines = list(csv.reader(io.StringIO(text, newline="")))
    except (UnicodeError, csv.Error) as exc:
        raise SchemaError("SOURCE_CSV_UNREADABLE") from exc
    if len(lines) < 62 or not lines[0] or lines[0][:2] != ["region_code","region_name"]:
        raise SchemaError("SOURCE_CSV_GEO_HEADER_BAD")
    ncols = len(lines[0])
    if ncols != len(set(lines[0])):
        raise SchemaError("DUPLICATE_FIELD")
    observed = set()
    for row in lines[1:]:
        if len(row) != ncols:
            raise SchemaError("ROW_WIDTH_DIFFERS")
        code, name = row[:2]
        if not name or (code and not GEO.fullmatch(code)):
            raise SchemaError("SOURCE_GEOGRAPHY_INVALID")
        if not code and name.strip().casefold() != "российская федерация" and "федеральный округ" not in name.casefold():
            raise SchemaError("UNEXPECTED_UNCODED_GEOGRAPHY")
        identity = (code,name)
        if identity in observed: raise SchemaError("DUPLICATE_SOURCE_GEOGRAPHY")
        observed.add(identity)
        if any(not val.isdecimal() for val in row[2:]):
            raise SchemaError("NON_INTEGER_SOURCE_OBSERVATION")
    if lines[1][1].strip().casefold() != "российская федерация":
        raise SchemaError("RUSSIA_NOT_FIRST")
    return lines

def validate_canonical(contents):
    """The current CSV can be sparse, but may contain only approved fields."""
    lines = _read_csv(contents)
    fields = lines[0]
    if not fields[2:]:
        raise SchemaError("CANONICAL_MEASURES_MISSING")
    valid = set(KINDS.values())
    slugs = set()
    for col in fields[2:]:
        m = FIELD_PATTERN.fullmatch(col)
        if m is None or m.group(2) not in valid:
            raise SchemaError("NONCANONICAL_FIELD:" + col)
        if col in slugs:
            raise SchemaError("DUPLICATE_CANONICAL_FIELD")
        slugs.add(col)
    expected = sorted(slugs, key=canonical_sort_key)
    if fields[2:] != expected:
        raise SchemaError("CANONICAL_FIELD_ORDER_INVALID")
    if "le_not_ceased__all" not in fields:
        raise SchemaError("CANONICAL_NATIONAL_MEASURE_MISSING")
    rows = {(r[0],r[1]):tuple(r) for r in lines[1:]}
    return fields, rows

def canonical_sort_key(column):
    m = FIELD_PATTERN.fullmatch(column)
    if m is None: raise SchemaError("CANONICAL_COLUMN_UNKNOWN")
    construct, slug = m.groups()
    return MEASURE_ORDER.index(construct), KIND_ORDER.index(
        next(code for code in KINDS if KINDS[code] == slug))

def convert(d, source_contents):
    """Source CSV -> canonical columns; every copied value remains byte-identical."""
    lines = _read_csv(source_contents)
    header = lines[0]
    e = epoch(d)
    destinations = {}
    dropped = []
    for i, col in enumerate(header[2:], start=2):
        new, disposition = mapping(d,col)
        if new is None:
            dropped.append({"source_field": col, "reason": disposition})
        else:
            if new in destinations:
                raise SchemaError("MULTIPLE_SOURCE_FIELDS_SAME_CONSTRUCT:" + new)
            destinations[new] = (i,col)
    if not destinations or "le_not_ceased__all" not in destinations:
        raise SchemaError("CANONICAL_SOURCE_TOTAL_NOT_FOUND")
    ordered = sorted(destinations, key=canonical_sort_key)
    retained = [{"source_field": destinations[col][1], "canonical_field": col,
                 "operation": "reported_value_alias"} for col in ordered]
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["region_code","region_name"] + ordered)
    for row in lines[1:]:
        writer.writerow(row[:2] + [row[destinations[col][0]] for col in ordered])
    result = output.getvalue().encode("utf-8")
    new_fields, new_rows = validate_canonical(result)
    if len(new_rows) != len(lines) - 1:
        raise SchemaError("CONVERSION_GEOGRAPHIC_ROWS_CHANGED")
    for old, new in zip(lines[1:], list(new_rows.values())):
        if tuple(old[:2]) != new[:2]:
            raise SchemaError("CONVERSION_SOURCE_ROW_ORDER_CHANGED")
        if any(old[destinations[col][0]] != new[j+2] for j,col in enumerate(ordered)):
            raise SchemaError("CONVERSION_RETAINED_NUMBER_CHANGED")
    return result, {
        "epoch":e,
        "map_version":MAP_VERSION,
        "source_csv_sha256":hashlib.sha256(source_contents).hexdigest(),
        "canonical_csv_sha256":hashlib.sha256(result).hexdigest(),
        "rows":len(lines)-1,
        "source_columns":len(header),
        "canonical_columns":len(new_fields),
        "retained_fields":retained,
        "omitted_fields":dropped,
    }

def compare(old, candidate):
    _, fresh = validate_canonical(candidate)
    if old is None:
        return "NEW", len(fresh)
    a, past = validate_canonical(old)
    b, _ = validate_canonical(candidate)
    if a != b:
        # A genuine *new* published source classification is an explicit
        # schema event, not a reason to erase previously retained observations.
        raise SchemaError("CANONICAL_SCHEMA_CHANGED_REQUIRES_REVIEW")
    changed = sum(past.get(k) != fresh.get(k) for k in past.keys() | fresh.keys())
    if not changed and list(past) != list(fresh): changed = 1
    return ("UPDATED" if changed else "NO_CHANGE", changed)
