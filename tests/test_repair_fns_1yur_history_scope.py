"""Source-kind eligibility and surgical correction regression tests."""
import csv
import io
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import capture_fns_1yur as modern
import capture_fns_1yur_history as history
import repair_fns_1yur_history_scope as repair


class KindEligibility(unittest.TestCase):
    def test_registration_record_count_is_not_a_legal_entity_kind(self):
        self.assertTrue(history.is_registration_record_label(
            "Общее количество записей о регистрации юридических лиц"))
        self.assertTrue(history.is_registration_record_label(
            "Количество записей о государственной регистрации юридических лиц"))
        self.assertTrue(history.is_registration_record_label(
            "Количество регистрационных записей юридических лиц"))

    def test_registration_process_related_types_are_not_removed(self):
        for label in (
            "Количество юридических лиц, сведения о которых содержатся в ЕГРЮЛ - ВСЕГО",
            "юридические лица, регистрируемые в соответствии со специальным порядком (Росрегистрация)",
            "Коммерческие организации, зарегистрированные в соответствии с отдельным порядком",
            "Общества с ограниченной ответственностью",
        ):
            self.assertFalse(history.is_registration_record_label(label), label)


def source_fixture():
    kinds = [str(1010 + n) for n in range(14)]
    header = ["region_code", "region_name"] + [
        "c01_" + k for k in kinds] + ["c01_1040", "c11_1010"]
    rows = [header]
    geos = [("", "Российская Федерация"),
            ("", "Центральный федеральный округ")]
    geos.extend((str(i).zfill(2), "Субъект " + str(i)) for i in range(1, 61))
    geos.append(("50", "Субъект 50 совместно с иным периметром"))
    for n, (code, name) in enumerate(geos):
        rows.append([code, name] + [str(n * 100 + k) for k in range(len(kinds))]
                    + [str(n * 5000), str(n)])
    o = io.StringIO(newline="")
    w = csv.writer(o, lineterminator="\n")
    w.writerows(rows)
    return o.getvalue().encode("utf-8")


class Correction(unittest.TestCase):
    def test_only_registration_record_column_removed(self):
        source = source_fixture()
        result, removed, rows = repair.prune_csv(source, {"1040"})
        self.assertEqual(removed, ["c01_1040"])
        self.assertEqual(rows, 63)
        old_h, old = modern.read_csv(source)
        new_h, new = modern.read_csv(result)
        self.assertNotIn("c01_1040", new_h)
        self.assertEqual(len(new_h), len(old_h) - 1)
        self.assertEqual(list(old), list(new))
        for geo in old:
            self.assertEqual(new[geo], tuple(
                old[geo][index] for index, col in enumerate(old_h) if col != "c01_1040"))
        self.assertEqual(modern.compare(result, result), ("NO_CHANGE", 0))

    def test_blank_or_missing_bankruptcy_is_not_filled_with_zero(self):
        source = source_fixture()
        fixed, _, _ = repair.prune_csv(source, {"1040"})
        cols, _ = modern.read_csv(fixed)
        self.assertEqual([x for x in cols if x.startswith("c11_")], ["c11_1010"])
        self.assertNotIn("c11_1040", cols)
        self.assertFalse(any(x.startswith("c08_") for x in cols))

    def test_missing_non_entity_source_column_fails_closed(self):
        source = source_fixture()
        with self.assertRaisesRegex(history.HistoryError, "NON_ENTITY_COLUMNS_NOT_FOUND"):
            repair.prune_csv(source, {"1050"})


if __name__ == "__main__":
    unittest.main()
