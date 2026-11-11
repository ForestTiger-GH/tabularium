"""Offline source, ZIP, Excel-schema and semantic CSV tests for FNS Form 1-YUR."""
from datetime import date
import io
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import capture_fns_1yur as src

DAY = date(2026, 11, 1)
KINDS = list(src.KINDS_2026)
REGIONS = [str(i).zfill(2) for i in range(1, 61)]


def fake_rows():
    return {
        region: {"name": "Region " + region, "kinds": {
            kind: {"c01": "1", "c08": "0", "c12": "0"} for kind in KINDS
        }} for region in REGIONS
    }


class FakeSheet:
    ncols = 14

    def __init__(self, mode, key, mismatch=False):
        self.mode = mode
        self.key = key
        self.mismatch = mismatch
        self.nrows = 101 if mode == "kind" else 48

    def cell_value(self, row, col):
        if self.mode == "kind":
            if row == 9:
                return {2: 1, 9: 8, 13: 12}.get(col, "")
            if row == 10:
                return {2: 60, 9: 0, 13: 0}.get(col, "")
            if row in range(12, 72):
                region = REGIONS[row - 12]
                return {0: region, 1: "Region " + region, 2: 1,
                        9: 0, 13: 0}.get(col, "")
            return ""
        if row == 8:
            return {2: 1, 9: 8, 13: 12}.get(col, "")
        if row in range(9, 9 + len(KINDS)):
            kind = KINDS[row - 9]
            val = 2 if self.mismatch and row == 9 and col == 2 else 1
            return {1: int(kind), 2: val, 9: 0, 13: 0}.get(col, "")
        return ""


class FakeBook:
    def __init__(self, mismatch=False):
        self.sheets = {k: FakeSheet("kind", k) for k in KINDS}
        self.sheets["1300"] = FakeSheet("kind", "1300")
        self.sheets.update({
            k: FakeSheet("region", k, mismatch=mismatch and k == REGIONS[0])
            for k in REGIONS
        })

    def sheet_names(self):
        return list(self.sheets)

    def sheet_by_name(self, name):
        return self.sheets[name]

    def release_resources(self):
        pass


class Discovery(unittest.TestCase):
    def test_fns_details_anchor_uses_preceding_date(self):
        page = src.page_url(2026)
        html = ('<html><ul><li>Сведения по состоянию на 01.11.2026 '
                '<a href="/html/sites/www.new.nalog.ru/files/related_activities/'
                'statistics_and_analytics/forms/reg/1ur11_26.zip">Подробнее</a></li>'
                '<li>Сведения по состоянию на 01.10.2026 '
                '<a href="/html/sites/www.new.nalog.ru/files/related_activities/'
                'statistics_and_analytics/forms/reg/1ur10_26.zip">Подробнее</a></li>'
                '</ul></html>').encode()
        found = src.extract_releases(html, page)
        self.assertEqual(set(found), {date(2026, 11, 1), date(2026, 10, 1)})
        self.assertTrue(found[DAY].endswith("1ur11_26.zip"))

    def test_fail_closed_empty_publication_page(self):
        with self.assertRaisesRegex(src.SourceError, "SOURCE_RELEASE_LINKS_MISSING"):
            src.extract_releases(b"<html>maintenance</html>", src.page_url(2026))

    def test_no_guessing_unknown_year(self):
        with self.assertRaisesRegex(src.SourceError, "YEAR_PAGE_NOT_REVIEWED"):
            src.page_url(2017)


class Archives(unittest.TestCase):
    def build_zip(self, *names):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as z:
            for name in names:
                z.writestr(name, src.OLE + b"source")
        return output.getvalue()

    def test_index_one_not_first_file(self):
        data = self.build_zip("Отчет 1-ЮР_2026_11_01.xls",
                              "Отчет 1-ЮР_2026_11_01(1).xls")
        blob, name = src.choose_member(data, DAY)
        self.assertEqual(name, "Отчет 1-ЮР_2026_11_01(1).xls")
        self.assertEqual(blob, src.OLE + b"source")

    def test_ambiguous_or_missing_selected_member(self):
        data = self.build_zip("Отчет 1-ЮР_2026_11_01.xls")
        with self.assertRaisesRegex(src.SourceError, "ARCHIVE_MEMBER_MISSING_OR_AMBIGUOUS"):
            src.choose_member(data, DAY)
        data = self.build_zip("Отчет 1-ЮР_2026_11_01(1).xls",
                              "Отчет 1-ЮР_2026_11_01 (1).xls")
        # No fallback from an unrecognized alternative to a second member.
        self.assertEqual(src.choose_member(data, DAY)[1], "Отчет 1-ЮР_2026_11_01(1).xls")

    def test_member_date_conflict_blocks_capture(self):
        with self.assertRaisesRegex(src.SourceError, "ARCHIVE_MEMBER_DATE_CONFLICT"):
            src.choose_member(self.build_zip("Отчет 1-ЮР_2026_10_01(1).xls"), DAY)


class SourceObservations(unittest.TestCase):
    def extract(self, mismatch=False):
        module = types.SimpleNamespace(open_workbook=lambda **kw: FakeBook(mismatch=mismatch))
        with patch.dict(sys.modules, {"xlrd": module}):
            return src.extract_xls(src.OLE + b"fake", DAY)

    def test_three_indicators_every_kind_and_double_orientation(self):
        rows, kinds = self.extract()
        self.assertEqual(len(rows), 60)
        self.assertEqual(len(kinds), 37)
        data = src.write_csv(rows, kinds)
        header, parsed = src.read_csv(data)
        self.assertEqual(len(header), 113)
        self.assertEqual(len(parsed), 60)
        self.assertEqual(src.compare(None, data), ("NEW", 60))
        self.assertEqual(src.compare(data, data), ("NO_CHANGE", 0))

    def test_disagreement_blocks_publication(self):
        with self.assertRaisesRegex(src.SourceError, "CROSS_ORIENTATION_MISMATCH"):
            self.extract(mismatch=True)

    def test_content_change_not_byte_metadata(self):
        rows = fake_rows()
        before = src.write_csv(rows, KINDS)
        rows["01"]["kinds"]["1000"]["c08"] = "1"
        after = src.write_csv(rows, KINDS)
        self.assertEqual(src.compare(before, after), ("UPDATED", 1))
        header, parsed = src.read_csv(after)
        self.assertEqual(parsed["01"][header.index("c08_1000")], "1")

    def test_no_implicit_null_to_zero(self):
        rows = fake_rows()
        rows["01"]["kinds"]["1000"]["c12"] = ""
        with self.assertRaisesRegex(src.SourceError, "CSV_COUNT_INVALID"):
            src.read_csv(src.write_csv(rows, KINDS))

    def test_region_string_codes_preserved(self):
        rows = fake_rows()
        csv = src.write_csv(rows, KINDS).decode("utf-8")
        self.assertIn("\n01,Region 01,", csv)
        self.assertIn("c01_1000", csv.splitlines()[0])
        self.assertIn("c12_1251", csv.splitlines()[0])


if __name__ == "__main__":
    unittest.main()
