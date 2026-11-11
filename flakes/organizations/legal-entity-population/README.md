# FNS Form 1-YUR — dated legal-entity observations

Source-traceable **CSV representations** of Part I of the Russian Federal Tax Service (FNS) Form 1-YUR, with official reference dates from 2012-01-01 onward. These are not original FNS CSV files. The original published XLS, RAR, ZIP or OOXML is read transiently; the retained observations are copied without numerical adjustment or new calculated measures.

Each `YYYY/YYYY-MM-DD_1-YUR.csv` contains the exact geographic rows in the source's order: Russian Federation first, federal-district aggregates in their published positions, and territorial / composite-perimeter rows. Publication-date gaps are not filled; no suitable Part I stock source is available for 2015-07-01.

## CSV field contract

The first two columns remain `region_code` and `region_name`. The source reporting territory code is **not OKTMO** and is not necessarily unique. Uncoded Russia/district aggregates use an empty code. The combination of date, physical row position, code and original name identifies a published geographic observation; do not merge or re-sort rows by code.

All other columns use `le_<measure>__<kind>` with **one reported source value per field**. These canonical headings are identity-only aliases for the actually published field in the source's own dated classification. No arithmetic, backfilling, multiplication, subtraction, status inference, normalization or null-to-zero conversion is allowed.

| Measure in the CSV | Meaning |
| --- | --- |
| `le_not_ceased__*` | Legal entities whose activities are *not registered as ceased* at the snapshot date under that source edition's rules; **not** equivalent to economically active businesses. |
| `le_bankruptcy_proceedings__*` | Entities under procedures applied in bankruptcy cases at the reference date, when published. This is a status, **not** new bankruptcies over the month. |
| `le_ceased_bankruptcy_liquidation__*` | Entities with cessation through liquidation in bankruptcy as reported in Part I. This is **not** the number of newly opened bankruptcy cases in the month. |

The suffix `all` is the total FNS legal-entity population, `commercial` and `nonprofit` are its two source-reported components. Additional suffixes correspond to the 2026 source category dictionary below. Nested categories overlap: adding all 37 legal kinds would greatly overstate totals.

### Current (2026) source-kind dictionary

The following suffixes are stable field identifiers for the **2026 classification**, *not* a claim that matching source names in 2012–2025 used identical methodological rules. Their source legal-kind codes remain visible through the per-release mapping manifest.

| 2026 FNS kind | Canonical suffix (after double underscore) | FNS category / limitation |
| --- | --- | --- |
| 1000 | `all` | All registered legal entities in the selected Part I perimeter |
| 1100 | `commercial` | Commercial organizations, aggregate |
| 1110 | `general_partnership` | General partnerships |
| 1120 | `limited_partnership` | Limited partnerships (partnerships on faith) |
| 1130 | `limited_liability_company_including_additional` | LLC group, **including** additional-liability company subtype |
| 1131 | `additional_liability_company` | Additional-liability subtype of 1130; **not additive** |
| 1140 | `joint_stock_company` | Joint-stock companies, aggregate |
| 1141 | `public_joint_stock_company` | Public joint-stock companies |
| 1142 | `nonpublic_joint_stock_company` | Non-public joint-stock companies |
| 1143 | `open_joint_stock_company` | Open joint-stock companies; legacy legal form |
| 1144 | `closed_joint_stock_company` | Closed joint-stock companies; legacy legal form |
| 1150 | `production_cooperative` | Production cooperatives |
| 1151 | `agricultural_production_cooperative` | Agricultural production cooperative subset of 1150 |
| 1160 | `peasant_farm_enterprise` | Peasant (farm) enterprises |
| 1170 | `unitary_enterprise` | Unitary enterprises, aggregate |
| 1171 | `federal_unitary_enterprise` | Federal unitary enterprises |
| 1172 | `regional_unitary_enterprise` | Unitary enterprises of constituent entities |
| 1173 | `municipal_unitary_enterprise` | Municipal unitary enterprises |
| 1174 | `federal_treasury_enterprise` | Federal treasury enterprises |
| 1175 | `regional_treasury_enterprise` | Treasury enterprises of constituent entities |
| 1176 | `municipal_treasury_enterprise` | Municipal treasury enterprises |
| 1180 | `other_commercial` | Other commercial organizations, current residual category |
| 1190 | `special_registration_commercial_cbr` | Special-registration commercial organizations, Bank of Russia |
| 1200 | `nonprofit` | Nonprofit organizations, aggregate |
| 1210 | `consumer_cooperative` | Consumer cooperatives |
| 1220 | `real_estate_owners_association` | Real-estate owners' associations |
| 1221 | `gardening_nonprofit_association` | Gardening / vegetable-growing / dacha nonprofits |
| 1222 | `homeowners_association` | Homeowners' associations |
| 1230 | `institution` | Institutions, aggregate |
| 1231 | `federal_institution` | Federal institutions |
| 1232 | `regional_institution` | Institutions of constituent entities |
| 1233 | `municipal_institution` | Municipal institutions |
| 1240 | `special_registration_nonprofit` | Special-registration nonprofits, aggregate |
| 1241 | `special_registration_nonprofit_justice_ministry` | Ministry-of-Justice special-registration nonprofits |
| 1242 | `special_registration_nonprofit_cbr` | Bank-of-Russia special-registration nonprofits |
| 1250 | `other_nonprofit` | Other nonprofit organizations, current residual category |
| 1251 | `personal_foundation` | Personal foundations, a subset of 1250 when reported |

The source worksheets for 1174–1176 have contradictory row-3 descriptions in the reviewed November 2026 workbook. The national summary provides the definitions above; values were copied under their **printed kind codes**, never silently corrected.

## Historical field mapping and irreversible exclusions

The single [field-provenance.json](field-provenance.json) records, **for every reference date**, the old `cNN_KKKK` source header, canonical heading, old/new CSV SHA-256, exact row count, taxonomy epoch and **every omitted historical field**. It is the machine-readable map from canonical representation back to the captured source-code representation (recoverable through the pre-migration Git commit). The implementation is [fns_1yur_semantics.py](../../../scripts/fns_1yur_semantics.py).

| Source dates | Source taxonomy | Total / commercial / nonprofit codes | Source measure codes |
| --- | --- | --- | --- |
| 2012-01 to 2013-04 | A | 1010 / 1020 / **1030** | Not ceased: 01; ceased by bankruptcy: 11 |
| 2013-05 to 2019-02 | B | 1010 / 1020 / **1040** | Not ceased: 01; ceased by bankruptcy: 11 |
| 2019-03 to 2021-01 | C1 | 1000 / 1100 / 1200 | Not ceased: 01; ceased by bankruptcy: 12 |
| 2021-02 to 2023-01 | C2 | 1000 / 1100 / 1200 | Not ceased: 01; in bankruptcy: 09; ceased by bankruptcy: 13 |
| 2023-02 onward | C3 | 1000 / 1100 / 1200 | Not ceased: 01; in bankruptcy: 08; ceased by bankruptcy: 12 |

A source column is renamed only if its actual publication edition supplies a reviewed direct reported-value category aligned to the current suffix. An old category without a defensible direct modern alias is **omitted entirely**, not populated as zero. No historical numbers are recalculated. In particular:

- Before 2013-05, kind **1030 means all nonprofits**. From 2013-05 through 2019-02, it means *other commercial organizations*; nonprofits move to 1040. The historic `c01_1030` values must never form one series across that boundary.
- Before 2013-05, 1024 is joint-stock companies; from 2013-05, 1024 is additional-liability companies. Other legal-kind codes also shifted in May 2013.
- In the 2013-05–2019-02 edition, kind 1023 covers LLC **excluding** separately published additional-liability entities, whereas today's 1130 includes the latter. That historical 1023 field has **no reported-only direct equivalent** to the modern 1130 and is omitted. A sum of 1023+1024 could only exist in a separate, explicitly **derived** analytical layer.
- Old residual `other commercial` / `other nonprofit` categories are not automatically mapped to new residual categories because their membership changes with the classification.
- Unreported status/construct fields are absent from the CSV. 2019-06-01 retains only two measures for the overall kind: source subcategory worksheets lack complete territorial coverage. A missing column is **not** a zero and the source is not patched.

Historical headings can share an analytical name without proving fully identical economic constructs: reporting statuses, registry definitions, legal classifications and territorial coverage can change. In 2023-02 the geographic publication expands by four source regions (90, 93, 94, 95); national and regional levels must not be compared across that boundary without an explicit reproducible bridge.

Some earlier editions assign the same source code to differently scoped territories, such as code 50 for Moscow Oblast alone and for Moscow Oblast together with Baikonur, or code 29 for Arkhangelsk Oblast alone and with Nenets AO. **Both original rows stay in their published positions.** Russia and federal-district aggregates are source rows, not values recalculated from the subregions. Source-internal control-sheet disagreements remain documented in the operational event log.

## Capture and verification

The [historical source reader](../../../scripts/capture_fns_1yur_history.py) reads only identifiable FNS Part I source workbooks, including documented legacy publisher format quirks. The [scheduled capture adapter](../../../scripts/capture_fns_1yur.py) creates the **same canonical columns** using the reviewed mapping for that reference date; unknown indicator codes or ambiguous mappings fail closed. The [publication monitor](../../../_mw/work/publication-monitor/README.md) shares the existing five UTC schedules with the FNS SME and other source checks.

For each official source issue, the operational publication event records the publisher URL, source member and SHA-256, extract method, reference date, source and canonical mapping version, and changes. The one-time `SCHEMA_MIGRATED` events record both historical CSV hashes and the manifest hash without Telegram alerts. The migration did not modify any retained numeric cell, geographic name/code or geographic row order; dropped columns are fully listed in the manifest.

This source is distinct from the FNS SME registry, which also includes individual entrepreneurs. Rates, monthly bankruptcy-flow estimates, cross-period territory corrections, inferred residual classes and other analytical calculations belong outside this evidence representation and require explicit provenance.

## Primary publication references

- [FNS Form 1-YUR 2026 releases](https://www.nalog.gov.ru/rn77/related_activities/statistics_and_analytics/forms/16601803/) — contemporary source and reference dates.
- [FNS Form 1-YUR 2025 releases](https://www.nalog.gov.ru/rn77/related_activities/statistics_and_analytics/forms/15764462/) — earlier source editions and year-boundary publication arrangement.
