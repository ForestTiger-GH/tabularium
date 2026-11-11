"""Resolve only the four migrated series' historical storage paths on reads.

Published FNS events and the Form 1-YUR snapshot manifest are immutable.
This helper is not a source registry, a general rewrite API or a bridge.
"""
from pathlib import Path

_CBR = "scrolls/russia/authorities/bank-of-russia/credit-institution-structural-units"
_LEGAL = "scrolls/russia/authorities/federal-tax-service/legal-entity-registration"
_SME = "scrolls/russia/authorities/federal-tax-service/sme-registry-statistics"
_NEW_DAILY = "flakes/banking/service-network/bank-regional-offices"
_NEW_MONTHLY = "flakes/banking/service-network/territorial-offices"
_NEW_LEGAL = "flakes/organizations/legal-entity-population"
_NEW_SME = "flakes/organizations/sme-register-population"


def current_csv_path(path: str | Path) -> str:
    value = Path(path).as_posix()
    if value.startswith(_CBR + "/"):
        if value.endswith("_OFFICES-REG.csv"):
            return _NEW_MONTHLY + value[len(_CBR):]
        if value.endswith("_OFFICES.csv"):
            return _NEW_DAILY + value[len(_CBR):]
        return value
    if value.startswith(_LEGAL + "/"):
        return _NEW_LEGAL + value[len(_LEGAL):]
    if value.startswith(_SME + "/"):
        return _NEW_SME + value[len(_SME):]
    return value
