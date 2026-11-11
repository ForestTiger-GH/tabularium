# Bank-by-region offices

Bank × region source-table observations (`_OFFICES.csv`).

`YYYY-MM-DD_OFFICES.csv` is an extraction of the Bank of Russia's [bank-by-region HTML table](https://www.cbr.ru/banking_sector/credit/cstat/). The filename identifies the fixed UTC+03 retrieval date of automated captures; retrospectively uploaded historical CSVs retain the date labels supplied with their historical files, which do not independently establish the true retrieval date. Every published bank-by-region data row appears once.

The first two columns, `source_row` and `section_label`, are traceability fields: `source_row` is the physical source row (HTML for automatic captures, XLSX worksheet for earlier converted snapshots); `section_label` is the preceding territorial section label. Some older publications have an empty label rather than the later literal `-`, and neither may be silently substituted for the other. Subsequent columns retain the source's actual published headers and ordering. Early forms include office categories absent in later forms; names and values are not retroactively harmonized.

The extraction decodes HTML entities and folds layout whitespace, but does not calculate or infer values; blank, `0` and `—` remain distinct. Rows are observed on the extraction date, not necessarily the source's statistical reference date. Context outside the HTML table is not archived. The [collector](../../../../scripts/capture_cbr_offices.py) and [daily workflow](../../../../.github/workflows/capture-cbr-offices.yml) capture at 01:17 UTC (04:17 UTC+03). The [read-only monitor](../../../../.github/workflows/check-cbr-offices.yml) checks the day's file at 09:17 UTC.

The [monthly territorial series](../territorial-offices/) has a different reporting unit and reference-date meaning. Do not automatically combine or harmonize the two. Treat text identifiers literally and take care with source-leading spreadsheet formula characters.
