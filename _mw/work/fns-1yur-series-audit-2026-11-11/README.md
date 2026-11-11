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

## Source field transitions

- total: 2012-01-01: c01_1010, 2019-03-01: c01_1000
- status: 2021-02-01: c09_1000, 2023-02-01: c08_1000
- ceased: 2012-01-01: c11_1010, 2019-03-01: c12_1000, 2021-02-01: c13_1000, 2023-02-01: c12_1000

## Largest within-source monthly shocks

| Region | Metric | Date | Before | After | Change |
| --- | --- | --- | ---: | ---: | ---: |
| Башкортостан | c09_1000 | 2022-03-01 | 676 | 804 | +18.93% |
| Краснодарский край | c09_1000 | 2022-03-01 | 1,083 | 1,280 | +18.19% |
| Новосибирская область | c01_1010 | 2013-01-01 | 150,422 | 138,988 | -7.60% |
| Санкт-Петербург | c01_1010 | 2017-01-01 | 370,965 | 349,194 | -5.87% |
| Московская область | c01_1000 | 2019-10-01 | 199,388 | 209,771 | +5.21% |
| Москва | c01_1000 | 2019-06-01 | 783,086 | 746,354 | -4.69% |
| Москва | c01_1010 | 2016-10-01 | 1,025,965 | 982,251 | -4.26% |
| Татарстан | c01_1010 | 2017-08-01 | 123,088 | 118,032 | -4.11% |
| Москва | c01_1010 | 2016-09-01 | 1,069,408 | 1,025,965 | -4.06% |
| Москва | c01_1000 | 2021-10-01 | 591,045 | 567,695 | -3.95% |
| Свердловская область | c01_1010 | 2018-01-01 | 155,301 | 149,188 | -3.94% |
| Краснодарский край | c01_1000 | 2019-05-01 | 127,537 | 123,334 | -3.30% |
| Санкт-Петербург | c01_1010 | 2018-01-01 | 349,379 | 337,913 | -3.28% |
| Московская область | c01_1010 | 2012-08-01 | 227,772 | 220,506 | -3.19% |
| Новосибирская область | c01_1010 | 2019-01-01 | 115,165 | 111,502 | -3.18% |
| Москва | c01_1000 | 2020-08-01 | 677,360 | 656,665 | -3.06% |

## Interpretation boundaries

- Code 1010 (older) and 1000 (newer) name the broad legal-entity class in distinct source classifications. The figure is a provisional bridge, not proof of construct identity.
- In 2019-06, only the complete 1000 category is retained; missing category columns are absent, not zero.
- Moscow Oblast uses the uncombined row, not the source line including Baikonur.
- A gap in source bankruptcy-status reporting is not a zero. Some historical kinds have no bankruptcy columns.
- Changes in the geographic source name do not automatically establish changed territorial perimeter.
- Source national/district rows are not summed with constituent subjects.
- Same-field jumps are review flags; they do not establish ingestion failure without cross-checking the original source.
