# FNS Form 1-YUR: legal-entity registration by region

This series is a source-traceable, **partial representation**, not an original FNS CSV. It extracts monthly or historically available regional observations from the Federal Tax Service's official Form 1-YUR ZIP publications. The original ZIP and legacy XLS member are read transiently, validated, and not mirrored in this series.

## Scope and source identity

The reference date is the date of the FNS statistical snapshot, **not** the download date or the publication-page update timestamp. One current UTF-8, comma-delimited, LF-terminated CSV is stored at `YYYY/YYYY-MM-DD_1-YUR.csv`. A correction replaces the same dated file through a normal Git commit; no second revision file or count-history file is created.

Official publication pages include [2026](https://www.nalog.gov.ru/rn77/related_activities/statistics_and_analytics/forms/16601803/) and [2025](https://www.nalog.gov.ru/rn77/related_activities/statistics_and_analytics/forms/15764462/). A January snapshot may be linked from the preceding year's page. Published historical frequency is not guaranteed to be monthly; only source-linked reference dates are represented. The selected ZIP member must be the unambiguous Form 1-YUR workbook with suffix `(1).xls`. The source workbook name and SHA-256, the official source link, reference date, and output hash are recorded in the publication event. A regular automated capture additionally records the downloaded ZIP's SHA-256 and extractor commit. The initial 2026-11-01 sample was bootstrapped from a supplied FNS XLS: its exact workbook SHA-256 is preserved, while the unobserved ZIP SHA-256 and automated extractor revision are explicitly null. This initial event must not be misread as independent verification of the official ZIP bytes.

## Values and CSV columns

Each row represents one source-identified Russian federal subject as printed in the FNS release. Its first two columns are `region_code` and `region_name`, followed by all `c01_<legal-kind-code>`, all `c08_<legal-kind-code>`, and all `c12_<legal-kind-code>` columns in ascending legal-kind-code order.

- `c01`: FNS indicator **1**, legal entities entered in the register excluding those whose activity has ceased. It is neither all historical registrations nor necessarily an economically active-firms count.
- `c08`: FNS indicator **8**, legal entities undergoing procedures applied in bankruptcy cases; a point-in-time status.
- `c12`: FNS indicator **12**, legal entities that ceased activity through bankruptcy; **not** new bankruptcies in the reporting month. Interpret its reference-period accumulation only in the context of the particular FNS release.
- The suffix is the **code of the legal-entity-type sheet**, not its heading string. Categories are nested and can overlap; never sum the 37 columns to construct a total. The reviewed November 2026 issue has 37 legal-kind codes and 88 region rows, giving 113 columns.

The selection is by the indicator code in Excel row 10, verified against the reviewed C/J/N layout for the current form. Region-specific worksheets independently repeat legal-type rows and are cross-checked cell by cell against the legal-type worksheets; the national totals are reconciled against regional sums only when the source's disclosed territory perimeter supports that equality. The national worksheet and district subtotals are checks, not duplicated data rows. Sheet `1300` counts registration records rather than legal entities and is deliberately excluded.

Special source territory rows `96` (Sirius) and `99` (other territories, including Baikonur) are not forced into a federal subject. A nonzero selected count in either row blocks publication pending an explicit scope review. No fixed region count is projected backward through history. The headings of legal-type sheets `1174`, `1175`, and `1176` conflict with the corresponding descriptions in the source's national summary; only the codes identify CSV columns. This source discrepancy is preserved rather than silently corrected.

Zero is different from missing, omitted, blank, suppressed, unreported, or invalid. Only exact nonnegative integer values are retained. Unknown or changed layouts, ambiguous ZIP members, inconsistent regional/national totals, missing classifications, unexplained territorial changes, and failed double-entry cross-checks cause a **fail-closed** check: existing CSVs remain untouched. Historical classifications may differ; newly encountered layouts must be reviewed before their source representations are accepted.


## Column dictionary and legal-entity classification

The first two columns mean: \`region_code\` — the FNS reporting-territory code printed in the source (a string; not OKTMO), and \`region_name\` — the FNS source territory name verbatim. All remaining columns use exactly \`cNN_KKKK\`, where \`NN\` is the selected numbered indicator and \`KKKK\` is the four-digit **source worksheet / legal-kind code**. An example: \`c08_1130\` is FNS indicator 8 for limited liability companies. A code not published in a historical edition is **absent**, not zero.

| Prefix | FNS indicator | Published construct | Interpretation |
| --- | --- | --- | --- |
| \`c01\` | 1 | Legal entities with register entries, excluding entities that have ceased operations | Stock at the publication reference date, not an estimate of economically active enterprises |
| \`c08\` | 8 | Legal entities under procedures applied in bankruptcy cases | A status/stock in the published perimeter |
| \`c12\` | 12 | Legal entities whose activity ceased through bankruptcy | A cessation count as defined in the release, not automatically a monthly flow |

The following dictionary is transcribed in English from the **national summary sheet of the 2026-11-01 Form 1-YUR issue**, not inferred from an external economic taxonomy. It describes that source edition, **not a universal retroactive mapping for 2012–2025**. Historical names, category sets, boundaries, and underlying legal definitions can differ and must be checked against each release.

| Legal-kind code | Meaning in the 2026-11-01 FNS national summary | Relation / important caution |
| --- | --- | --- |
| \`1000\` | All legal entities | Aggregate, includes 1100 and 1200 |
| \`1100\` | Commercial organizations, total | Aggregate |
| \`1110\` | General partnerships | Component of 1100 |
| \`1120\` | Limited partnerships | Component of 1100 |
| \`1130\` | Limited liability companies | Component of 1100 |
| \`1131\` | Additional liability companies | Subset of 1130; do not sum with 1130 |
| \`1140\` | Joint-stock companies, total | Aggregate of 1141–1144 in the source edition |
| \`1141\` | Public joint-stock companies | Subset of 1140 |
| \`1142\` | Non-public joint-stock companies | Subset of 1140 |
| \`1143\` | Open joint-stock companies | Subset of 1140, legacy form |
| \`1144\` | Closed joint-stock companies | Subset of 1140, legacy form |
| \`1150\` | Production cooperatives (artels) | Component of 1100 |
| \`1151\` | Agricultural production cooperatives | Subset of 1150 |
| \`1160\` | Peasant (farm) enterprises | Component of 1100 in this edition |
| \`1170\` | Unitary enterprises | Aggregate of relevant subtypes |
| \`1171\` | Federal unitary enterprises | Subset of 1170 |
| \`1172\` | Unitary enterprises of constituent entities of Russia | Subset of 1170 |
| \`1173\` | Municipal unitary enterprises | Subset of 1170 |
| \`1174\` | Federal treasury enterprises | Subset of 1170; see source-header discrepancy below |
| \`1175\` | Treasury enterprises of constituent entities of Russia | Subset of 1170; see discrepancy |
| \`1176\` | Municipal treasury enterprises | Subset of 1170; see discrepancy |
| \`1180\` | Other commercial organizations | Component of 1100 |
| \`1190\` | Commercial organizations registered under a special procedure (Bank of Russia) | Independently published source category; not automatically additive to the printed 1100 components |
| \`1200\` | Non-profit organizations, total | Aggregate |
| \`1210\` | Consumer cooperatives | Component of 1200 |
| \`1220\` | Real-estate owners' associations | Component of 1200 |
| \`1221\` | Gardening, vegetable-growing or dacha non-profit associations | Subset of 1220 |
| \`1222\` | Homeowners' associations | Subset of 1220 |
| \`1230\` | Institutions, total | Aggregate |
| \`1231\` | Federal institutions | Subset of 1230 |
| \`1232\` | Institutions of constituent entities of Russia | Subset of 1230 |
| \`1233\` | Municipal institutions | Subset of 1230 |
| \`1240\` | Non-profit organizations registered under a special procedure, total | Aggregate |
| \`1241\` | Non-profit organizations registered under the special procedure of the Ministry of Justice | Subset of 1240 |
| \`1242\` | Non-profit organizations registered under the special procedure of the Bank of Russia | Subset of 1240 |
| \`1250\` | Other non-profit organizations | Component of 1200 |
| \`1251\` | Personal foundations | Subset of 1250, only when published in that edition |

The source summary contains explicit subtype relations and may include overlapping categories. Do **not** add all 37 category columns to estimate the total. In the 2026-11-01 workbook, the category sheets \`1174\`, \`1175\`, and \`1176\` carry contradictory / duplicated row-3 descriptions; the national summary gives the meanings above. The CSV preserves the sheet **codes** and published numeric values; the discrepancy is documented, not silently repaired. Sheet \`1300\` measures **registration records**, not entities, and is intentionally outside the selected 1/8/12 representation.

## Processing and limitations

The [source adapter](../../../../../scripts/capture_fns_1yur.py) handles publisher link discovery, bounded ZIP retrieval, XLS extraction, double-orientation validation, deterministic CSV output, and semantic comparison. [The publication monitor](../../../../../_mw/work/publication-monitor/README.md) integrates this independent source adapter into the established five daily UTC slots and uses a separate operational event/outbox and Telegram notification only **after successful corpus publication**. Local originals and ZIP/XLS parsing use a pinned `xlrd` dependency; no macros or formulas are executed.

This series differs from the FNS SME register: SME membership and all registered legal entities are different constructs; the SME series also includes individual entrepreneurs. Cross-series normalization, shares, rates, monthly bankruptcy changes, and reconciliations belong outside this evidence layer and require an explicit reproducible bridge. Published primary material may contain errors, and a successful technical validation does not certify a wider economic interpretation.

For important use, verify values and methodology against the relevant original FNS release. The original publisher's rights and legal status are not changed by inclusion in Tabularium.
