# AGENTS.md

## Repository purpose

tabularium is a public, source-faithful corpus of machine-readable primary publications and documented bridges to canonical high-volume primary datasets.

## Core rules

1. Store primary public-source artifacts only. A narrowly documented historical preservation proxy may be retained when the original primary publication is no longer publicly accessible. Preserve the proxy's actual publisher and provenance, and never represent it as the unavailable primary-source original.
2. A high-volume or frequently updated official primary dataset may be represented by a documented remote-source bridge instead of a mirrored artifact when the canonical publisher provides stable public access. A bridge must identify the canonical source, document retrieval and provenance rules, preserve source semantics, and must not present derived or analytical values as source data.
3. Preserve source meaning and reported values. Do not add analysis, interpretation, normalization, derived calculations, or private/internal data.
4. The authoritative source corpus lives under `scrolls/`. Route by country first unless an explicitly documented cross-country or source-institution route applies. `scrolls/world/` contains the documented non-Russian and international routes. Non-Russian corporate publications belong under `scrolls/world/corporate-disclosures/`; preserve the reporting-entity jurisdiction there with an ISO 3166-1 alpha-2 prefix in artifact names and registry metadata. Stable public-authority and survey source-institution routes live under the documented `authorities/` and `surveys/` containers; within those containers, the publisher or institution may be the durable routing axis. Within each route, use stable source classes documented by its README. Corporate financial reporting remains under its dedicated reporting family within both the Russian and world corporate-disclosure routes; recurring official publications may route by source institution and stable publication series. An established domain route may group closely related source institutions when explicitly documented by the route.
5. Do not add new industry or topic taxonomies to the physical directory tree unless the repository contract is explicitly revised. Existing documented domain routes are part of the repository contract.
6. Keep paths and repository control files in English, lowercase, and ASCII where practical.
7. Routing directories, stable publication-series directories, and bridge families must contain a minimal README.md. Period/issue directories do not require one.
8. Keep natively machine-readable source artifacts such as HTML, XLSX, CSV, XML, and JSON in their original format. Store PDF publications as complete source-faithful Markdown transcriptions.
9. Keep all artifacts belonging to the same publication issue or release together. A single-artifact issue may remain a period/date-named file; create an issue directory when a release contains multiple related artifacts.
10. Add new top-level taxonomies only when a real source class requires them. Avoid speculative empty structure.
11. Do not infer the licence or legal status of a third-party artifact from its inclusion in the repository or from the root LICENSE. The root CC0 dedication applies only to original Tabularium contributions as defined in NOTICE.md. Preserve source provenance and do not assign CC0 or other Tabularium licensing metadata to third-party or source-derived content unless that legal status is explicitly established.

## Current routes

- scrolls/russia/corporate-disclosures/financial-reporting/{ifrs,ras,ras-banks}/
- scrolls/russia/corporate-disclosures/{annual-reports,issuer-reports}/
- scrolls/russia/corporate-disclosures/strategies/{2024,2025,2026}/
- scrolls/russia/authorities/bank-of-russia/
- scrolls/russia/authorities/ministry-of-economic-development/
- scrolls/russia/authorities/rosstat/
- scrolls/russia/surveys/dom-rf-analytics/largest-mortgage-banks-results/
- scrolls/russia/surveys/stock-market/{moex-exchange,spb-exchange}/
- scrolls/world/corporate-disclosures/{financial-reporting,annual-reports}/
- scrolls/world/corporate-disclosures/strategies/{2024,2025,2026}/
- scrolls/world/authorities/
- scrolls/world/surveys/{usa-stanford,usa-mckinsey,icco}/

## Out of scope

Analytical work, research notes, transformed conclusions, internal methodologies, private data, and secondary-media retellings except the narrowly documented historical preservation-proxy case in Core rule 1.
