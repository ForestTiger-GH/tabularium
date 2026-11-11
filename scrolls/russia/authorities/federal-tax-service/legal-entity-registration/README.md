# FNS Form 1-YUR: legal-entity registration by region

This series is a source-traceable, **partial representation**, not an original FNS CSV. It extracts monthly or historically available regional observations from the Federal Tax Service's official Form 1-YUR ZIP publications. The original ZIP and legacy XLS member are read transiently, validated, and not mirrored in this series.

## Scope and source identity

The reference date is the date of the FNS statistical snapshot, **not** the download date or the publication-page update timestamp. One current UTF-8, comma-delimited, LF-terminated CSV is stored at `YYYY/YYYY-MM-DD_1-YUR.csv`. A correction replaces the same dated file through a normal Git commit; no second revision file or count-history file is created.

Official publication pages include [2026](https://www.nalog.gov.ru/rn77/related_activities/statistics_and_analytics/forms/16601803/) and [2025](https://www.nalog.gov.ru/rn77/related_activities/statistics_and_analytics/forms/15764462/). A January snapshot may be linked from the preceding year's page. Published historical frequency is not guaranteed to be monthly; only source-linked reference dates are represented. The selected ZIP member must be the unambiguous Form 1-YUR workbook with suffix `(1).xls`. Its original name and SHA-256, the official archive URL and SHA-256, the extractor revision, source reference date, and output hash are recorded in the publication event.

## Values and CSV columns

Each row represents one source-identified Russian federal subject as printed in the FNS release. Its first two columns are `region_code` and `region_name`, followed by all `c01_<legal-kind-code>`, all `c08_<legal-kind-code>`, and all `c12_<legal-kind-code>` columns in ascending legal-kind-code order.

- `c01`: FNS indicator **1**, legal entities entered in the register excluding those whose activity has ceased. It is neither all historical registrations nor necessarily an economically active-firms count.
- `c08`: FNS indicator **8**, legal entities undergoing procedures applied in bankruptcy cases; a point-in-time status.
- `c12`: FNS indicator **12**, legal entities that ceased activity through bankruptcy; **not** new bankruptcies in the reporting month. Interpret its reference-period accumulation only in the context of the particular FNS release.
- The suffix is the **code of the legal-entity-type sheet**, not its heading string. Categories are nested and can overlap; never sum the 37 columns to construct a total. The reviewed November 2026 issue has 37 legal-kind codes and 88 region rows, giving 113 columns.

The selection is by the indicator code in Excel row 10, verified against the reviewed C/J/N layout for the current form. Region-specific worksheets independently repeat legal-type rows and are cross-checked cell by cell against the legal-type worksheets; the national totals are reconciled against regional sums only when the source's disclosed territory perimeter supports that equality. The national worksheet and district subtotals are checks, not duplicated data rows. Sheet `1300` counts registration records rather than legal entities and is deliberately excluded.

Special source territory rows `96` (Sirius) and `99` (other territories, including Baikonur) are not forced into a federal subject. A nonzero selected count in either row blocks publication pending an explicit scope review. No fixed region count is projected backward through history. The headings of legal-type sheets `1174`, `1175`, and `1176` conflict with the corresponding descriptions in the source's national summary; only the codes identify CSV columns. This source discrepancy is preserved rather than silently corrected.

Zero is different from missing, omitted, blank, suppressed, unreported, or invalid. Only exact nonnegative integer values are retained. Unknown or changed layouts, ambiguous ZIP members, inconsistent regional/national totals, missing classifications, unexplained territorial changes, and failed double-entry cross-checks cause a **fail-closed** check: existing CSVs remain untouched. Historical classifications may differ; newly encountered layouts must be reviewed before their source representations are accepted.

## Processing and limitations

The [source adapter](../../../../../scripts/capture_fns_1yur.py) handles publisher link discovery, bounded ZIP retrieval, XLS extraction, double-orientation validation, deterministic CSV output, and semantic comparison. [The publication monitor](../../../../../_mw/work/publication-monitor/README.md) integrates this independent source adapter into the established five daily UTC slots and uses a separate operational event/outbox and Telegram notification only **after successful corpus publication**. Local originals and ZIP/XLS parsing use a pinned `xlrd` dependency; no macros or formulas are executed.

This series differs from the FNS SME register: SME membership and all registered legal entities are different constructs; the SME series also includes individual entrepreneurs. Cross-series normalization, shares, rates, monthly bankruptcy changes, and reconciliations belong outside this evidence layer and require an explicit reproducible bridge. Published primary material may contain errors, and a successful technical validation does not certify a wider economic interpretation.

For important use, verify values and methodology against the relevant original FNS release. The original publisher's rights and legal status are not changed by inclusion in Tabularium.
