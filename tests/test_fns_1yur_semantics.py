"""Offline regression tests for lossless FNS 1-YUR semantic harmonization."""
import csv
from datetime import date
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fns_1yur_semantics as f


def sample(day, types, metrics):
    head=["region_code","region_name"] + [
        "c" + str(metric).zfill(2) + "_" + code
        for metric in metrics for code in types
    ]
    rows=[
        ["", "Российская Федерация"],
        ["", "Центральный федеральный округ"],
    ]+[(str(n).zfill(2), "Субъект " + str(n))
       for n in range(1, 61)]
    b=io.StringIO(newline="")
    w=csv.writer(b,lineterminator="\n")
    w.writerow(head)
    for count,(code,name) in enumerate(rows):
        w.writerow([code,name]+[str(count * 1000 + i) for i in range(len(head)-2)])
    return b.getvalue().encode("utf-8")


class Epochs(unittest.TestCase):
    def test_exact_boundaries(self):
        for date_str, expected in (
            ("2012-01-01","A"),("2013-04-01","A"),
            ("2013-05-01","B"),("2019-02-01","B"),
            ("2019-03-01","C1"),("2021-01-01","C1"),
            ("2021-02-01","C2"),("2023-01-01","C2"),
            ("2023-02-01","C3"),("2026-11-01","C3"),
        ):
            self.assertEqual(f.epoch(date_str),expected)
        with self.assertRaisesRegex(f.SchemaError,"DATE_BEFORE"):
            f.epoch("2011-12-01")

    def test_may_2013_1030_semantic_reuse(self):
        self.assertEqual(f.mapping("2013-04-01","c01_1030")[0],"le_not_ceased__nonprofit")
        self.assertIsNone(f.mapping("2013-05-01","c01_1030")[0])
        self.assertEqual(f.mapping("2013-05-01","c01_1040")[0],"le_not_ceased__nonprofit")

    def test_reused_1024_not_persisted_as_same_company_type(self):
        self.assertEqual(f.mapping("2013-04-01","c01_1024")[0],
                         "le_not_ceased__joint_stock_company")
        self.assertEqual(f.mapping("2013-05-01","c01_1024")[0],
                         "le_not_ceased__additional_liability_company")
        self.assertEqual(f.mapping("2013-05-01","c01_1025")[0],
                         "le_not_ceased__joint_stock_company")

    def test_noncomparable_llc_only_not_falsely_renamed(self):
        self.assertEqual(f.mapping("2013-04-01","c01_1023")[0],
                         "le_not_ceased__limited_liability_company_including_additional")
        self.assertIsNone(f.mapping("2013-05-01","c01_1023")[0])
        self.assertEqual(f.mapping("2019-03-01","c01_1130")[0],
                         "le_not_ceased__limited_liability_company_including_additional")

    def test_bankruptcy_source_indicator_changes(self):
        values=[("2018-10-01","c11_1010"),("2020-10-01","c12_1000"),
                ("2022-10-01","c13_1000"),("2026-11-01","c12_1000")]
        for day, field in values:
            self.assertEqual(f.mapping(day,field)[0],
                             "le_ceased_bankruptcy_liquidation__all")
        self.assertEqual(f.mapping("2022-10-01","c09_1000")[0],
                         "le_bankruptcy_proceedings__all")
        self.assertEqual(f.mapping("2026-11-01","c08_1000")[0],
                         "le_bankruptcy_proceedings__all")

    def test_all_reported_modern_categories_have_unique_identifiers(self):
        names={f.mapping("2026-11-01","c01_"+code)[0]
               for code in f.KINDS}
        self.assertEqual(len(names),37)

    def test_unknown_indicator_is_rejected_not_removed(self):
        with self.assertRaisesRegex(f.SchemaError,"UNREVIEWED_SOURCE_INDICATOR"):
            f.mapping("2012-01-01","c12_1010")

    def test_source_row_values_and_order_preserved(self):
        raw=sample("2013-05-01",["1010","1020","1023","1024","1040","1030"],
                   [1,11])
        canonical, info=f.convert(date(2013,5,1),raw)
        header, observations=f.validate_canonical(canonical)
        self.assertEqual(info["epoch"],"B")
        self.assertEqual(info["rows"],62)
        self.assertNotIn("le_not_ceased__limited_liability_company_including_additional",header)
        self.assertIn("le_not_ceased__additional_liability_company",header)
        self.assertIn("le_not_ceased__nonprofit",header)
        self.assertEqual(len(info["omitted_fields"]),4)  # 2 unavailable kinds x 2 indicators
        self.assertEqual(next(iter(observations)),("", "Российская Федерация"))
        self.assertEqual(list(observations)[1],("", "Центральный федеральный округ"))
        self.assertEqual(f.compare(canonical,canonical),("NO_CHANGE",0))

    def test_no_unpublished_bankruptcy_status_fabricated(self):
        raw=sample("2012-02-01",["1010","1020","1030"],[1,11])
        canonical,info=f.convert("2012-02-01",raw)
        self.assertNotIn(b"le_bankruptcy_proceedings",canonical)
        self.assertEqual(len(info["retained_fields"]),6)

    def test_duplicate_approved_target_is_rejected(self):
        with self.assertRaisesRegex(f.SchemaError,"DUPLICATE_FIELD"):
            fake=sample("2019-03-01",["1000","1000"],[1,12])
            f.convert("2019-03-01",fake)

    def test_routine_source_capture_produces_canonical_csv(self):
        import capture_fns_1yur as source
        raw = sample("2026-11-01",["1000","1100","1200"],[1,8,12])
        with patch("capture_fns_1yur_history.capture",
                   return_value=(raw,{"regions":60,"legal_kinds":3})):
            rendered, meta = source.capture(date(2026,11,1),
                "https://www.nalog.gov.ru/html/sites/www.new.nalog.ru/files/related_activities/statistics_and_analytics/forms/reg/1ur11_26.zip")
        fields, rows = source.read_csv(rendered)
        self.assertEqual(len(rows),62)
        self.assertIn("le_bankruptcy_proceedings__all",fields)
        self.assertEqual(meta["semantic_map_version"],f.MAP_VERSION)
        self.assertEqual(len(meta["canonical_retained_fields"]),9)
        self.assertEqual(source.compare(rendered,rendered),("NO_CHANGE",0))

    def test_routine_can_refuse_mixing_old_and_current_schemas(self):
        import capture_fns_1yur as source
        raw = sample("2026-11-01",["1000","1100","1200"],[1,8,12])
        canonical, _ = f.convert("2026-11-01",raw)
        with self.assertRaisesRegex(source.SourceError,"SOURCE_CSV_UNREADABLE|NONCANONICAL_FIELD|ROW_WIDTH|SCHEMA"):
            source.compare(raw,canonical)

    def test_changed_geography_is_a_real_change(self):
        raw=sample("2026-11-01",["1000","1100","1200"],[1,8,12])
        same,info=f.convert("2026-11-01",raw)
        self.assertEqual(f.compare(same,same),("NO_CHANGE",0))


if __name__ == "__main__":
    unittest.main()
