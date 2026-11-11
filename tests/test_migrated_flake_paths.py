"""Regression tests for the four economic-series path migrations."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from migrated_flake_paths import current_csv_path


class EconomicRoutes(unittest.TestCase):
    def test_legacy_storage_paths_resolve_without_renaming_source_values(self):
        mappings = [
            ("scrolls/russia/authorities/bank-of-russia/credit-institution-structural-units/2026/2026-11-11_OFFICES.csv",
             "flakes/banking/service-network/bank-regional-offices/2026/2026-11-11_OFFICES.csv"),
            ("scrolls/russia/authorities/bank-of-russia/credit-institution-structural-units/2026/2026-11-01_OFFICES-REG.csv",
             "flakes/banking/service-network/territorial-offices/2026/2026-11-01_OFFICES-REG.csv"),
            ("scrolls/russia/authorities/federal-tax-service/legal-entity-registration/2026/2026-11-01_1-YUR.csv",
             "flakes/organizations/legal-entity-population/2026/2026-11-01_1-YUR.csv"),
            ("scrolls/russia/authorities/federal-tax-service/sme-registry-statistics/2026/2026-11-10_SME-REG.csv",
             "flakes/organizations/sme-register-population/2026/2026-11-10_SME-REG.csv"),
        ]
        for old, new in mappings:
            with self.subTest(old=old):
                self.assertEqual(current_csv_path(old), new)
                self.assertEqual(current_csv_path(new), new)

    def test_unrelated_paths_do_not_rewrite(self):
        paths = ("scrolls/russia/authorities/rosstat/README.md",
                 "scrolls/russia/authorities/bank-of-russia/credit-institution-structural-units/README.md",
                 "scrolls/russia/authorities/federal-tax-service/legal-entity-registration-extra/2015/a.csv")
        for path in paths:
            self.assertEqual(current_csv_path(path), path)


if __name__ == "__main__":
    unittest.main()
