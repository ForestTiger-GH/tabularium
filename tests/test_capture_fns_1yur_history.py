"""Source-geography / legacy metric regression tests; no network."""
from datetime import date
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import capture_fns_1yur as current
import capture_fns_1yur_history as historic


def fixture(sparse=True):
    kinds = [str(1000 + n) for n in range(15)]
    fields = ["region_code", "region_name"] + ["c01_" + n for n in kinds]
    if sparse:
        fields += ["c11_" + kinds[0]]
    data = [",".join(fields)]
    names = [("", "Российская Федерация"), ("", "Центральный федеральный округ")]
    names += [(str(n).zfill(2), f"Субъект {n}") for n in range(1, 61)]
    # Same code, different source perimeters; neither may overwrite the other.
    names += [("50", "Московская область и г.Байконур")]
    for code, name in names:
        data.append(",".join([code, name] +
                             ["1"] * (len(fields) - 2)))
    return "\n".join(data).encode() + b"\n"


class Geography(unittest.TestCase):
    def test_national_and_district_first_and_order_preserved(self):
        fields, rows = current.read_csv(fixture())
        self.assertEqual(next(iter(rows)), ("", "Российская Федерация"))
        self.assertEqual(list(rows)[1], ("", "Центральный федеральный округ"))
        self.assertEqual(list(rows)[2], ("01", "Субъект 1"))
        self.assertEqual(list(rows)[-1], ("50", "Московская область и г.Байконур"))
        self.assertEqual(len(fields), 18)
        self.assertEqual(len(rows), 63)

    def test_duplicate_code_is_not_duplicate_observation(self):
        _, rows = current.read_csv(fixture())
        self.assertIn(("50", "Субъект 50"), rows)
        self.assertIn(("50", "Московская область и г.Байконур"), rows)

    def test_reordering_is_a_content_update(self):
        data = fixture()
        lines = data.splitlines()
        swapped = b"\n".join(lines[:2] + [lines[3], lines[2]] + lines[4:]) + b"\n"
        status, count = current.compare(data, swapped)
        self.assertEqual(status, "UPDATED")
        self.assertGreaterEqual(count, 1)

    def test_absent_legacy_indicator_is_not_zero(self):
        header, _ = current.read_csv(fixture(sparse=True))
        self.assertIn("c11_1000", header)
        self.assertNotIn("c11_1001", header)
        self.assertNotIn("c08_1001", header)

    def test_unreported_cell_fails_closed(self):
        data = fixture().replace(b",1\n", b",\n", 1)
        with self.assertRaisesRegex(current.SourceError, "CSV_COUNT_INVALID"):
            current.read_csv(data)

    def test_exact_form_member_precedence(self):
        self.assertEqual(historic.member_name(["x_II.xls", "x_I.xls"]), "x_I.xls")
        self.assertEqual(historic.member_name(["x(2).xls", "x(1).xls"]), "x(1).xls")

    def test_no_historical_source_before_2012(self):
        with self.assertRaisesRegex(historic.HistoryError, "HISTORY_RANGE_INVALID"):
            historic.discover(date(2011, 12, 1), date(2012, 1, 1))


if __name__ == "__main__":
    unittest.main()
