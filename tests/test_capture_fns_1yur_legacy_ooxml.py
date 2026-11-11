"""Read official OOXML content mislabeled with .xls extensions in legacy 1-YUR ZIPs."""
import io
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import capture_fns_1yur as modern
import capture_fns_1yur_history as history


class LegacyWorkbook(unittest.TestCase):
    def fixture(self):
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Российская Федерация"
        ws.cell(1, 1).value = "Исходный заголовок"
        ws.cell(3, 2).value = "ФНС"
        ws.cell(5, 3).value = 34
        stream = io.BytesIO()
        wb.save(stream)
        return stream.getvalue()

    def test_xlsx_bytes_named_xls_are_read_only_and_natively_checked(self):
        body = self.fixture()
        self.assertTrue(body.startswith(b"PK"))
        self.assertTrue(history.is_spreadsheet_ooxml(body))
        book = history.open_source_workbook(body)
        try:
            sh = book.sheet_by_name("Российская Федерация")
            self.assertEqual(sh.nrows, 5)
            self.assertEqual(sh.cell_value(4, 2), 34)
            self.assertEqual(sh.cell_value(0, 0), "Исходный заголовок")
            self.assertEqual(sh.cell_value(0, 2), "")
            self.assertEqual(sh.cell_value(11, 5), "")
        finally:
            book.release_resources()

    def test_zip_with_source_member_index_one_named_xls(self):
        body = self.fixture()
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("report_I.xls", body)
            z.writestr("report_II.xls", body)
        raw, name, outer = history.workbook_from_asset(
            archive.getvalue(),
            "https://www.nalog.gov.ru/html/sites/www.new.nalog.ru/svod/1_ur_2018_04.zip")
        self.assertEqual(name, "report_I.xls")
        self.assertEqual(outer, "zip")
        self.assertEqual(raw, body)

    def test_generic_zip_is_not_a_spreadsheet(self):
        z = io.BytesIO()
        with zipfile.ZipFile(z, "w") as archive:
            archive.writestr("other.txt", "not a spreadsheet")
        self.assertFalse(history.is_spreadsheet_ooxml(z.getvalue()))
        with self.assertRaisesRegex(history.HistoryError, "SOURCE_WORKBOOK_TYPE_UNSUPPORTED"):
            history.open_source_workbook(z.getvalue())

    def test_legacy_biff_is_not_ooxml(self):
        self.assertFalse(history.is_spreadsheet_ooxml(modern.OLE + b"source"))


if __name__ == "__main__":
    unittest.main()
