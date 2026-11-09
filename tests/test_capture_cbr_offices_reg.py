"""Offline acceptance tests for the CBR territorial monthly collector."""
import csv
from datetime import date
import hashlib
import io
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'capture_cbr_offices_reg.py'
if not SCRIPT.exists():
    SCRIPT = Path(__file__).parent / 'capture_cbr_offices_reg.py'
spec = importlib.util.spec_from_file_location('cbr_reg', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def sample_xlsx(formula=False, extra_sheet=False, two_level=True):
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    workbook = f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Региональный разрез" sheetId="1" r:id="rId1"/></sheets></workbook>'
    relations = '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    def string(col, rid, val):
        return f'<c r="{col}{rid}" t="inlineStr"><is><t>{val}</t></is></c>'
    def num(col, rid, val):
        return f'<c r="{col}{rid}"><v>{val}</v></c>'
    rows = [f'<row r="1">{string("A",1,"Статистика территориального присутствия")}</row>']
    rows.append(f'<row r="2">{string("A",2,"Территория")}{string("B",2,"Кредитные организации")}{string("C",2,"Филиалы")}{string("D",2,"Мобильные офисы")}{string("E",2,"Всего")}</row>')
    regions = ['Российская Федерация'] + ['Белгородская область', 'Брянская область', 'Республика Алтай'] * 15
    for i, reg in enumerate(regions, 3):
        form = '<f>2+3</f>' if formula and i == 3 else ''
        rows.append(f'<row r="{i}">{string("A",i,reg)}{num("B",i,2)}{num("C",i,3)}<c r="D{i}">{form}<v>5</v></c>{num("E",i,10)}</row>')
    sheet = f'<worksheet xmlns="{ns}"><sheetData>{"".join(rows)}</sheetData></worksheet>'
    buff = io.BytesIO()
    with zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('xl/workbook.xml', workbook)
        z.writestr('xl/_rels/workbook.xml.rels', relations)
        z.writestr('xl/worksheets/sheet1.xml', sheet)
    return buff.getvalue()


def sample_page():
    links = ''.join(f'<a href="/vfs/statistics/bank_system/DivisionsPerRegion_01{mo:02d}20.xlsx">2020 г.: на 01.{mo:02d}</a>' for mo in range(1, 13))
    links += '<a href="/vfs/statistics/bank_system/DivisionsPerRegion_010719.xlsx">2019 г.: на 01.07</a>'
    links += '<a href="/vfs/statistics/bank_system/DivisionsPerRegion_011026.xlsx">2026 г.: на 01.10</a>'
    return '<html><body>' + links + '</body></html>'


class Parsing(unittest.TestCase):
    def test_source_link_dates_immutable(self):
        x = m.discover(sample_page())
        self.assertEqual(len(x), 14)
        self.assertEqual(max(x), date(2026, 10, 1))
        self.assertEqual(m.output_name(max(x)), '2026-10-01_OFFICES-REG.csv')
        with self.assertRaisesRegex(m.CaptureError, 'INVALID_SOURCE_URL'):
            m.url_date('https://evil.example/DivisionsPerRegion_011026.xlsx')
        with self.assertRaisesRegex(m.CaptureError, 'SOURCE_LINK_DATE_MISMATCH'):
            m.discover(sample_page().replace('2026 г.: на 01.10', '2026 г.: на 01.09'))

    def test_full_wide_csv_preserves_cells(self):
        blob = m.convert_xlsx(sample_xlsx())
        self.assertEqual(m.validate_csv(blob), 46)
        rs = list(csv.reader(io.StringIO(blob.decode('utf-8'))))
        self.assertEqual(rs[0], ['source_row','section_label','Территория','Кредитные организации','Филиалы','Мобильные офисы','Всего'])
        self.assertEqual(rs[1], ['3','','Российская Федерация','2','3','5','10'])
        self.assertEqual(rs[-1][2], 'Республика Алтай')
        self.assertEqual(rs[-1][5], '5')

    def test_formula_cached_value_and_source_formula_preserved(self):
        rows = list(csv.reader(io.StringIO(m.convert_xlsx(sample_xlsx(formula=True)).decode('utf-8'))))
        self.assertEqual(rows[1][6], '10')
        self.assertEqual(rows[1][5], '5')
        data, lineage = m.convert_xlsx(sample_xlsx(formula=True), return_formula_lineage=True)
        self.assertEqual(data, m.convert_xlsx(sample_xlsx(formula=True)))
        self.assertEqual(lineage['3']['4']['formula'], '2+3')
        self.assertEqual(lineage['3']['4']['attributes'], {})
        self.assertNotIn('source_formulas', rows[0])

    def test_formula_without_cached_value_rejected(self):
        original = sample_xlsx(formula=True)
        with zipfile.ZipFile(io.BytesIO(original)) as z:
            files = {n: z.read(n) for n in z.namelist()}
        files['xl/worksheets/sheet1.xml'] = files['xl/worksheets/sheet1.xml'].replace(
            b'<f>2+3</f><v>5</v>', b'<f>2+3</f>')
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w') as z:
            for name, data in files.items():
                z.writestr(name, data)
        with self.assertRaisesRegex(m.CaptureError, 'XLSX_FORMULA_CACHE_MISSING'):
            m.convert_xlsx(out.getvalue())

    def test_lookalike_zip_rejected(self):
        with self.assertRaises((m.CaptureError, zipfile.BadZipFile)):
            m.convert_xlsx(b'PK\x03\x04not-a-valid-file')

    def test_territorial_data_after_footer_is_rejected(self):
        base = sample_xlsx()
        with zipfile.ZipFile(io.BytesIO(base)) as source:
            data = {name: source.read(name) for name in source.namelist()}
        sheet = data['xl/worksheets/sheet1.xml'].decode('utf-8')
        extra = ('<row r="49"><c r="A49" t="inlineStr"><is><t>Notes</t></is></c></row>'
                 '<row r="50"><c r="A50" t="inlineStr"><is><t>Тюменская область</t></is></c>'
                 '<c r="B50"><v>2</v></c><c r="C50"><v>7</v></c></row>')
        data['xl/worksheets/sheet1.xml'] = sheet.replace('</sheetData>', extra+'</sheetData>').encode()
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as target:
            for name, value in data.items():
                target.writestr(name, value)
        with self.assertRaisesRegex(m.CaptureError, 'XLSX_DATA_AFTER_FOOTER'):
            m.convert_xlsx(out.getvalue())

    def test_daily_catches_up_missed_months(self):
        sample = sample_page().replace('</body>',
            '<a href="/vfs/statistics/bank_system/DivisionsPerRegion_010926.xlsx">2026 г.: на 01.09</a></body>')
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            published = root / 'published' / '2026'
            published.mkdir(parents=True)
            (published / '2026-08-01_OFFICES-REG.csv').write_bytes(m.convert_xlsx(sample_xlsx()))
            output = root / 'output'
            output.mkdir()
            with patch.object(m, 'CORPUS', str(root / 'published')), patch.object(
                    m, 'download', side_effect=lambda url, *_: sample.encode() if url == m.SOURCE_PAGE else sample_xlsx()):
                items = m.collect('daily', None, None, output)
            self.assertEqual([x['file'] for x in items],
                             ['2026-09-01_OFFICES-REG.csv', '2026-10-01_OFFICES-REG.csv'])

    def test_csv_values_not_inferred(self):
        original = m.convert_xlsx(sample_xlsx())
        altered = original.replace(b',2,3,5,10\n', b',2,3,,10\n', 1)
        self.assertEqual(m.validate_csv(altered), 46)
        self.assertNotEqual(original, altered)

    def test_only_table_and_source_headers_are_in_csv(self):
        from xml.etree import ElementTree as ET
        original = sample_xlsx()
        with zipfile.ZipFile(io.BytesIO(original)) as source:
            parts = {name: source.read(name) for name in source.namelist()}
        sheet = parts['xl/worksheets/sheet1.xml'].decode('utf-8')
        # The third physical row is the Excel column-number guide, not headings.
        guide = '<row r="2"><c r="A2"><v>1</v></c><c r="B2"><v>2</v></c></row>'
        sheet = sheet.replace('</sheetData>', '<row r="49"><c r="A49" t="inlineStr">'
                              '<is><t>Explanatory notes</t></is></c></row></sheetData>')
        parts['xl/worksheets/sheet1.xml'] = sheet.encode()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as target:
            for name, value in parts.items():
                target.writestr(name, value)
        rows = list(csv.reader(io.StringIO(m.convert_xlsx(buf.getvalue()).decode())))
        self.assertEqual(rows[0][2], 'Территория')
        self.assertEqual(len(rows), 47)
        self.assertFalse(any('Статистика территориального присутствия' in str(row)
                             or 'Explanatory notes' in str(row) for row in rows))

    def test_dynamic_district_label_and_four_ungrouped_tail_rows(self):
        original = sample_xlsx()
        with zipfile.ZipFile(io.BytesIO(original)) as source:
            parts = {name: source.read(name) for name in source.namelist()}
        ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
        sheet = ET.fromstring(parts['xl/worksheets/sheet1.xml'])
        district_row = next(row for row in sheet.find(ns+'sheetData')
                            if row.get('r') == '4')
        for cell in district_row.findall(ns+'c'):
            cell_ref = cell.get('r')
            if cell_ref == 'A4':
                cell.find(ns+'is').find(ns+'t').text = 'ПРИМЕР ФЕДЕРАЛЬНЫЙ ОКРУГ'
            elif cell_ref in ('B4', 'C4', 'D4', 'E4'):
                cell.find(ns+'v').text = {'B4':'80', 'C4':'120',
                                           'D4':'200', 'E4':'400'}[cell_ref]
        parts['xl/worksheets/sheet1.xml'] = ET.tostring(sheet, encoding='utf-8')
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as target:
            for name, value in parts.items():
                target.writestr(name, value)
        records = list(csv.reader(io.StringIO(m.convert_xlsx(buf.getvalue()).decode())))
        indexed = {int(row[0]): row for row in records[1:]}
        self.assertEqual(len(indexed), 45)
        self.assertNotIn(4, indexed)  # The district's subtotal is a section label.
        for i in range(5, 45):
            self.assertEqual(indexed[i][1], 'ПРИМЕР ФЕДЕРАЛЬНЫЙ ОКРУГ')
        for i in range(45, 49):
            self.assertEqual(indexed[i][1], '')
        self.assertFalse(any(row[2] == 'ПРИМЕР ФЕДЕРАЛЬНЫЙ ОКРУГ'
                             for row in records[1:]))

    def test_bad_final_district_balance_fails_closed(self):
        data = [(1, {1: 'ПРИМЕР ФЕДЕРАЛЬНЫЙ ОКРУГ', 2: '10', 3: '20'}),
                (2, {1: 'Территория', 2: '3', 3: '4'}),
                (3, {1: 'Территория', 2: '5', 3: '6'})]
        with self.assertRaisesRegex(m.CaptureError, 'XLSX_FINAL_DISTRICT_BALANCE_AMBIGUOUS'):
            m.last_district_boundary(data, 0, 1, [2, 3])

    def test_collect_keeps_formula_lineage_outside_csv(self):
        original = sample_xlsx(formula=True)
        with tempfile.TemporaryDirectory() as t:
            directory = Path(t)
            with patch.object(m, 'CORPUS', str(directory / 'empty-archive')), patch.object(
                    m, 'download', side_effect=lambda url, *_: sample_page().encode()
                    if url == m.SOURCE_PAGE else original):
                manifest = m.collect('backfill', date(2026,10,1), date(2026,10,1), directory)
            self.assertEqual(len(manifest), 1)
            self.assertEqual(manifest[0]['formula_cells']['3']['4']['formula'], '2+3')
            rows = list(csv.reader(io.StringIO(
                (directory / '2026-10-01_OFFICES-REG.csv').read_text(encoding='utf-8'))))
            self.assertEqual(rows[0][:3], ['source_row', 'section_label', 'Территория'])
            self.assertEqual(rows[1][5], '5')

    def test_old_three_metadata_columns_are_not_accepted(self):
        original = m.convert_xlsx(sample_xlsx())
        rows = list(csv.reader(io.StringIO(original.decode('utf-8'))))
        old = [['source_sheet', 'source_row', 'source_formulas'] + rows[0][1:]]
        old += [['Лист1', row[0], ''] + row[1:] for row in rows[1:]]
        with self.assertRaisesRegex(m.CaptureError, 'CSV_HEADER_INVALID'):
            m.validate_csv(m.serialize(old))

    def test_nonconsecutive_numeric_column_guide_is_not_a_header(self):
        """Column guides 1,2,3,4,9 must not leak into the source headings."""
        original = sample_xlsx()
        ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
        with zipfile.ZipFile(io.BytesIO(original)) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
        sheet = ET.fromstring(files['xl/worksheets/sheet1.xml'])
        sheet_data = sheet.find(ns + 'sheetData')
        for row in sheet_data.findall(ns + 'row'):
            number = int(row.get('r'))
            if number >= 3:
                row.set('r', str(number + 1))
                for cell in row.findall(ns + 'c'):
                    old_ref = cell.get('r')
                    cell.set('r', old_ref.rstrip('0123456789') + str(number + 1))
        ordinal = ET.Element(ns + 'row', {'r': '3'})
        for letter, value in [('A', '1'), ('B', '2'), ('C', '3'), ('D', '4'), ('E', '9')]:
            cell = ET.SubElement(ordinal, ns + 'c', {'r': letter + '3'})
            ET.SubElement(cell, ns + 'v').text = value
        sheet_data.insert(2, ordinal)
        files['xl/worksheets/sheet1.xml'] = ET.tostring(sheet, encoding='utf-8')
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        converted = m.convert_xlsx(buffer.getvalue())
        table = list(csv.reader(io.StringIO(converted.decode('utf-8'))))
        self.assertEqual(table[0], [
            'source_row', 'section_label', 'Территория', 'Кредитные организации',
            'Филиалы', 'Мобильные офисы', 'Всего'])
        self.assertEqual(len(table) - 1, 46)
        self.assertEqual(table[1][0], '4')
        self.assertEqual(m.validate_csv(converted), 46)

    def test_corrected_historical_headers_contain_no_excel_ordinal_suffixes(self):
        root = Path(__file__).resolve().parents[1] / m.CORPUS
        affected = ['2022-04-01', '2022-05-01', '2023-01-01',
                    '2023-02-01', '2023-08-01', '2023-10-01', '2023-12-01']
        for d in affected:
            path = root / d[:4] / (d + '_OFFICES-REG.csv')
            with self.subTest(date=d):
                with path.open('r', encoding='utf-8', newline='') as handle:
                    header = next(csv.reader(handle))
                self.assertFalse(any(' / ' in col and col.rsplit(' / ', 1)[-1].isdigit()
                                     for col in header[2:]))
                self.assertEqual(header[:2], ['source_row', 'section_label'])

    def test_daily_only_latest_and_backfill_skips_present(self):
        xlsx = sample_xlsx()
        with tempfile.TemporaryDirectory() as t:
            directory = Path(t)
            with patch.object(m, 'CORPUS', str(directory / 'empty-archive')), patch.object(m, 'download', side_effect=lambda url, *_: sample_page().encode() if url == m.SOURCE_PAGE else xlsx):
                manifest = m.collect('daily', None, None, directory)
            self.assertEqual(len(manifest), 1)
            self.assertEqual(manifest[0]['file'], '2026-10-01_OFFICES-REG.csv')
            self.assertEqual(manifest[0]['xlsx_sha256'], hashlib.sha256(xlsx).hexdigest())
            self.assertEqual(m.validate_csv((directory / '2026-10-01_OFFICES-REG.csv').read_bytes()), 46)


if __name__ == '__main__':
    unittest.main()
