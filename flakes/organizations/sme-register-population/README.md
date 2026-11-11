# SME registry statistics: regional monthly snapshots

This series preserves the Federal Tax Service's officially published counts of subjects of small and medium-sized entrepreneurship, as **source-traceable CSV representations**, one file per official source date under `YYYY/YYYY-MM-DD_SME-REG.csv`. The source is the [FNS SME statistics page](https://rmsp.nalog.ru/statistics.html); the adapter retrieves its regional aggregate records from `POST https://rmsp.nalog.ru/statistics-proc.json`, using form field `statDate=DD.MM.YYYY`. A CSV is not an official source CSV and does not reproduce the complete publication or all JSON fields.

Each UTF-8 CSV is comma-separated with an LF newline and one line per **region** (`cnt_level=0`). National totals, the nine published district/group subtotals, and indicators outside the counts scope are not stored as rows. Regional identifiers and names are retained from the source's `ssrf` and `name`; no district is inferred. Coverage is publication-specific (for example, 84 regional records for 2016-08-01 and 89 for 2026-11-10). Regional code is a string, not a normalized administrative identifier; names follow the published release.

| CSV column | FNS JSON key | Source meaning |
| --- | --- | --- |
| `region_code` | `ssrf` | Published region code |
| `region_name` | `name` | Published region name |
| `total` | `cnt_total` | All SME-register subjects |
| `ul_micro` | `cnt_ul_micro` | Legal entities, micro |
| `ul_small` | `cnt_ul_mini` | Legal entities, small |
| `ul_medium` | `cnt_ul_normal` | Legal entities, medium |
| `ip_micro` | `cnt_ip_micro` | Individual entrepreneurs, micro |
| `ip_small` | `cnt_ip_mini` | Individual entrepreneurs, small |
| `ip_medium` | `cnt_ip_normal` | Individual entrepreneurs, medium |

The first row is the table header. Rows are ordered by literal region code to make comparison deterministic. Published counts may appear as JSON integer values or decimal strings; both are represented as exact base-ten integer text without arithmetic derivation. Missing and zero are distinct: missing required counts invalidate capture, and totals are **validated**, never calculated to populate data. The source's `stat_date` must match the requested date for every row. The published display field `cnt_name` is verified to exist but is not forced to equal `name`: before October 2021, for example, the capitalization of the city prefix differed between the two fields for Moscow, Saint Petersburg, and Sevastopol. The CSV retains `name` verbatim. An unrecognized source schema, missing regions or inconsistent totals must not silently overwrite a valid CSV.

The [collector](../../../scripts/capture_fns_sme.py) creates candidate CSVs; the [publication monitor](../../../_mw/work/publication-monitor/README.md) checks the most recent published dates several times per day and can explicitly backfill historical release dates selected from the publisher's date control. **There is one current CSV for each official date.** If counts for the same date change, its contents are replaced in-place with an ordinary Git commit; no duplicate revision file or separate values history is stored. An unchanged recheck writes no file. Temporary raw responses are discarded after validation. Retrieval time, endpoint, request, source SHA-256, candidate CSV SHA-256, code revision, and publication status are recorded in the corresponding operational publication event and commit. They are not repeated in each data row. An operational event is not an additional observation.

The CSV excludes employees, social enterprise status, newly established subjects and all other statistical indicators. A subject's presence in this register does **not** mean it is the same construct as all registered firms, and a change in register counts does not by itself prove openings/closures. Historical geography and classification are not harmonized. Do not sum territorially nested values without reviewing the primary source. String cells can begin with spreadsheet formula characters; they are left source-faithful and must be handled safely by downstream spreadsheet software.

Official date, perimeter, definitions and any material source revision should be independently verified against the publisher before consequential use. Reference checks in November 2026 confirmed the JSON region fields and their correspondence with the FNS XLSX tables for selected national and regional rows; no universal API stability guarantee is implied.
