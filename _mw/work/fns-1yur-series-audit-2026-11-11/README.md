# FNS 1-YUR: monthly 2012–2026 regional series QA

Development-layer, exploratory observation; not a replacement or correction of source evidence.
178 dated source CSVs. The missing July 2015 publication is not imputed.
All source values are unchanged; metric-code crosswalk is an analytical interpretation only.

## Plots

- [Major regions: non-ceased legal entities](01_legal_entities_regions.png)
- [Major regions: bankruptcy proceedings](02_bankruptcy_status_regions.png)
- [Major regions: ceased via bankruptcy](03_bankruptcy_cessation_regions.png)
- [Monthly stock changes (heatmap)](04_mom_changes_heatmap.png)
- [Russian Federation: original national rows](05_russia_totals.png)
- [Confirmed 2019 and 2023 source-break checks](06_confirmed_source_breaks.png)

## Source-methodology epoch transitions

- total: 2012-01-01: epoch A: le_not_ceased__all, 2013-05-01: epoch B: le_not_ceased__all, 2019-03-01: epoch C1: le_not_ceased__all, 2021-02-01: epoch C2: le_not_ceased__all, 2023-02-01: epoch C3: le_not_ceased__all
- status: 2012-01-01: epoch A: None, 2013-05-01: epoch B: None, 2019-03-01: epoch C1: None, 2021-02-01: epoch C2: le_bankruptcy_proceedings__all, 2023-02-01: epoch C3: le_bankruptcy_proceedings__all
- ceased: 2012-01-01: epoch A: le_ceased_bankruptcy_liquidation__all, 2013-05-01: epoch B: le_ceased_bankruptcy_liquidation__all, 2019-03-01: epoch C1: le_ceased_bankruptcy_liquidation__all, 2021-02-01: epoch C2: le_ceased_bankruptcy_liquidation__all, 2023-02-01: epoch C3: le_ceased_bankruptcy_liquidation__all

## Known changes in source coverage

2023-02: the FNS geographic perimeter changes from 93 to 97 rows. The new source codes 90, 93, 94 and 95 report 31,805 legal entities combined. The national level changes 3,197,542 to 3,227,373 (+29,831); excluding the four newly appearing territory rows gives -1,974. This is a derived perimeter check, not a source-adjusted series.

2019-03: source classification changes from c01_1010 to c01_1000, and bankruptcy cessation changes from c11_1010 (249,949) to c12_1000 (227,557), a nominal -8.96% discontinuity. This cannot be interpreted as the actual disappearance of past bankruptcies.


## Largest within-source monthly shocks

| Region | Metric | Date | Before | After | Change |
| --- | --- | --- | ---: | ---: | ---: |
| Bashkortostan | le_bankruptcy_proceedings__all | 2022-03-01 | 676 | 804 | +18.93% |
| Krasnodar Krai | le_bankruptcy_proceedings__all | 2022-03-01 | 1,083 | 1,280 | +18.19% |
| Novosibirsk Oblast | le_not_ceased__all | 2013-01-01 | 150,422 | 138,988 | -7.60% |
| Saint Petersburg | le_not_ceased__all | 2017-01-01 | 370,965 | 349,194 | -5.87% |
| Moscow Oblast | le_not_ceased__all | 2019-10-01 | 199,388 | 209,771 | +5.21% |
| Moscow | le_not_ceased__all | 2019-06-01 | 783,086 | 746,354 | -4.69% |
| Moscow | le_not_ceased__all | 2016-10-01 | 1,025,965 | 982,251 | -4.26% |
| Tatarstan | le_not_ceased__all | 2017-08-01 | 123,088 | 118,032 | -4.11% |
| Moscow | le_not_ceased__all | 2016-09-01 | 1,069,408 | 1,025,965 | -4.06% |
| Moscow | le_not_ceased__all | 2021-10-01 | 591,045 | 567,695 | -3.95% |
| Sverdlovsk Oblast | le_not_ceased__all | 2018-01-01 | 155,301 | 149,188 | -3.94% |
| Krasnodar Krai | le_not_ceased__all | 2019-05-01 | 127,537 | 123,334 | -3.30% |
| Saint Petersburg | le_not_ceased__all | 2018-01-01 | 349,379 | 337,913 | -3.28% |
| Moscow Oblast | le_not_ceased__all | 2012-08-01 | 227,772 | 220,506 | -3.19% |
| Novosibirsk Oblast | le_not_ceased__all | 2019-01-01 | 115,165 | 111,502 | -3.18% |
| Moscow | le_not_ceased__all | 2020-08-01 | 677,360 | 656,665 | -3.06% |

## Interpretation boundaries

- Canonical aliases do not prove uniform economic constructs across A, B, C1, C2 and C3 source-method epochs. The source column lineage remains in field-provenance.json.
- In 2019-06, only complete overall-kind categories are retained; missing category fields are absent, not zero.
- Moscow Oblast uses the uncombined row, not the source line including Baikonur.
- A gap in source bankruptcy-status reporting is not a zero. Some historical kinds have no bankruptcy columns.
- Changes in the geographic source name do not automatically establish changed territorial perimeter.
- Source national/district rows are not summed with constituent subjects.
- Only month-on-month changes within the same source-method epoch are ranked; jumps across epoch boundaries are excluded.
