"""Offline tests for source-faithful FNS statistics capture."""
import csv
from datetime import date
import hashlib
from io import StringIO
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import capture_fns_sme as fns


def fixture(d=date(2026, 11, 10), count=89, *, as_strings=False):
    day = d.strftime("%d.%m.%Y") + " 00:00:00"
    regional = []
    for i in range(1, count + 1):
        vals = {
            "stat_date": day, "cnt_level": 0,
            "ssrf": str(i).zfill(2), "name": f"Region {i:02d}",
            "cnt_name": f"Region {i:02d}",
            "cnt_total": 101, "cnt_ul_total": 51,
            "cnt_ip_total": 50, "cnt_ul_micro": 40,
            "cnt_ul_mini": 10, "cnt_ul_normal": 1,
            "cnt_ip_micro": 45, "cnt_ip_mini": 4, "cnt_ip_normal": 1,
        }
        if as_strings:
            for k in list(vals):
                if k.startswith("cnt_") and k != "cnt_name" and k != "cnt_level":
                    vals[k] = str(vals[k])
        regional.append(vals)
    national = {"stat_date": day, "cnt_level": 2,
                "cnt_name": "Российская Федерация",
                "cnt_total": 101 * count,
                "cnt_ul_total": 51 * count,
                "cnt_ip_total": 50 * count}
    districts = [{"stat_date": day, "cnt_level": 1,
                  "cnt_name": f"District {i}"} for i in range(9)]
    return [national] + districts + regional


def encoded(items):
    return json.dumps(items, ensure_ascii=False).encode("utf-8")


class Dates(unittest.TestCase):
    def test_discovery_uses_actual_select_values(self):
        page = b'<select><option value="10.11.2026">10.11.2026</option><option value="01.08.2016">01.08.2016</option></select>'
        self.assertEqual(fns.discover_dates(html=page),
                         [date(2016, 8, 1), date(2026, 11, 10)])

    def test_unavailable_dates_cannot_be_invented(self):
        with self.assertRaisesRegex(fns.FnsError, "SOURCE_DATES_UNAVAILABLE"):
            fns.discover_dates(html=b"<html>maintenance</html>")

    def test_reference_date_not_capture_date(self):
        path = fns.file_for(date(2026, 11, 10))
        self.assertEqual(path.as_posix().split("/")[-2:], ["2026", "2026-11-10_SME-REG.csv"])
        self.assertEqual(fns.file_for(date(2016, 8, 1)).name, "2016-08-01_SME-REG.csv")


class Extract(unittest.TestCase):
    def test_early_2016_and_2026_schema(self):
        for d, size, strings in ((date(2016, 8, 1), 84, False),
                                 (date(2026, 11, 10), 89, True)):
            data = encoded(fixture(d, size, as_strings=strings))
            rows = fns.decode_snapshot(data, d)
            self.assertEqual(len(rows), size)
            self.assertEqual(rows["01"], ("01", "Region 01", "101", "40",
                                          "10", "1", "45", "4", "1"))

    def test_encoding_is_deterministic_and_order_irrelevant(self):
        rows = fixture()
        a = fns.write_csv(fns.decode_snapshot(encoded(rows), date(2026, 11, 10)))
        reversed_rows = [rows[0]] + rows[1:10] + list(reversed(rows[10:]))
        b = fns.write_csv(fns.decode_snapshot(encoded(reversed_rows), date(2026, 11, 10)))
        self.assertEqual(a, b)
        self.assertEqual(fns.compare(a, b), ("NO_CHANGE", 0))
        self.assertIn(b"region_code,region_name,total", a)

    def test_single_value_edit_and_region_name_edit(self):
        rows = fixture()
        a = fns.write_csv(fns.decode_snapshot(encoded(rows), date(2026, 11, 10)))
        rows[10]["cnt_ul_micro"] = 39
        rows[10]["cnt_ul_mini"] = 11
        b = fns.write_csv(fns.decode_snapshot(encoded(rows), date(2026, 11, 10)))
        self.assertEqual(fns.compare(a, b), ("UPDATED", 1))
        self.assertEqual(fns.compare(None, b), ("NEW", 89))
        rows[10]["name"] = "Revised Region"
        rows[10]["cnt_name"] = "Revised Region"
        c = fns.write_csv(fns.decode_snapshot(encoded(rows), date(2026, 11, 10)))
        self.assertEqual(fns.compare(b, c), ("UPDATED", 1))

    def test_numerical_zero_not_missing(self):
        rows = fixture()
        rows[10]["cnt_ul_normal"] = 0
        rows[10]["cnt_ul_mini"] = 11
        out = fns.decode_snapshot(encoded(rows), date(2026, 11, 10))
        self.assertEqual(out["01"][5], "0")
        rows[10]["cnt_ul_normal"] = None
        with self.assertRaisesRegex(fns.FnsError, "COUNT_NOT_NONNEGATIVE_INTEGER"):
            fns.decode_snapshot(encoded(rows), date(2026, 11, 10))

    def test_source_date_mismatch(self):
        rows = fixture()
        rows[10]["stat_date"] = "10.10.2026 00:00:00"
        with self.assertRaisesRegex(fns.FnsError, "SOURCE_DATE_MISMATCH"):
            fns.decode_snapshot(encoded(rows), date(2026, 11, 10))

    def test_duplicate_region_cannot_be_written(self):
        rows = fixture()
        rows[11]["ssrf"] = "01"
        with self.assertRaisesRegex(fns.FnsError, "REGION_DUPLICATE"):
            fns.decode_snapshot(encoded(rows), date(2026, 11, 10))

    def test_total_reconciliation(self):
        rows = fixture()
        rows[10]["cnt_total"] = 102
        with self.assertRaisesRegex(fns.FnsError, "SOURCE_TOTAL_INCONSISTENT"):
            fns.decode_snapshot(encoded(rows), date(2026, 11, 10))

    def test_reject_truncated_region_set_and_bad_existing_csv(self):
        new = fns.write_csv(fns.decode_snapshot(encoded(fixture(count=80)), date(2026, 11, 10)))
        old = fns.write_csv(fns.decode_snapshot(encoded(fixture(count=89)), date(2026, 11, 10)))
        with self.assertRaisesRegex(fns.FnsError, "SOURCE_REGION_DROP_UNEXPECTED"):
            fns.compare(old, new)
        with self.assertRaisesRegex(fns.FnsError, "CSV_HEADER_INVALID"):
            fns.compare(b"foo,bar\n", new)

    def test_reject_malformed_or_html_body(self):
        with self.assertRaisesRegex(fns.FnsError, "JSON_INVALID"):
            fns.decode_snapshot(b"<html>challenge</html>", date(2026, 11, 10))
        with self.assertRaisesRegex(fns.FnsError, "SOURCE_ROWS_INVALID"):
            fns.decode_snapshot(b"[]", date(2026, 11, 10))

    def test_csv_roundtrip_and_excel_formula_name_not_silently_modified(self):
        rows = fixture()
        rows[10]["name"] = "=source label"
        rows[10]["cnt_name"] = "=source label"
        b = fns.write_csv(fns.decode_snapshot(encoded(rows), date(2026, 11, 10)))
        self.assertEqual(fns.read_csv(b)["01"][1], "=source label")

    def test_no_network_needed_for_unit_extraction(self):
        sample = encoded(fixture())
        with patch.object(fns, "get_official", return_value=sample) as get:
            out, sha = fns.capture(date(2026, 11, 10))
            self.assertEqual(sha, hashlib.sha256(sample).hexdigest())
            self.assertEqual(len(fns.read_csv(out)), 89)
            self.assertEqual(get.call_count, 1)


if __name__ == "__main__":
    unittest.main()
