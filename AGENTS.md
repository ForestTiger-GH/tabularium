# AGENTS.md

## Repository purpose

tabularium is a public, source-faithful corpus of machine-readable primary publications and documented bridges to canonical high-volume primary datasets.

## Core rules

1. Store primary public-source artifacts only. A narrowly documented historical preservation proxy may be retained when the original primary publication is no longer publicly accessible. Preserve the proxy's actual publisher and provenance, and never represent it as the unavailable primary-source original.
2. A high-volume or frequently updated official primary dataset may be represented by a documented remote-source bridge instead of a mirrored artifact when the canonical publisher provides stable public access. A bridge must identify the canonical source, document retrieval and provenance rules, preserve source semantics, and must not present derived or analytical values as source data.
3. Preserve source meaning and reported values. Do not add analysis, interpretation, normalization, derived calculations, or private/internal data.
4. Route by country first. Within a country, use stable routes documented by that country. Corporate financial reporting remains under its dedicated reporting family within russia/corporate-disclosures/; recurring official publications may route by source institution and stable publication series. An established domain route may group closely related source institutions when explicitly documented by the country route.
5. Do not add new industry or topic taxonomies to the physical directory tree unless the repository contract is explicitly revised. Existing documented domain routes are part of the repository contract.
6. Keep paths and repository control files in English, lowercase, and ASCII where practical.
7. Routing directories, stable publication-series directories, and bridge families must contain a minimal README.md. Period/issue directories do not require one.
8. Keep natively machine-readable source artifacts such as HTML, XLSX, CSV, XML, and JSON in their original format. Store PDF publications as complete source-faithful Markdown transcriptions.
9. Keep all artifacts belonging to the same publication issue or release together. A single-artifact issue may remain a period/date-named file; create an issue directory when a release contains multiple related artifacts.
10. Add new top-level taxonomies only when a real source class requires them. Avoid speculative empty structure.
11. Do not infer the licence or legal status of a third-party artifact from its inclusion in the repository or from the root LICENSE. The root CC0 dedication applies only to original Tabularium contributions as defined in NOTICE.md. Preserve source provenance and do not assign CC0 or other Tabularium licensing metadata to third-party or source-derived content unless that legal status is explicitly established.

## Current routes

- russia/corporate-disclosures/financial-reporting/{ifrs,ras,ras-banks}/
- russia/corporate-disclosures/{annual-reports,issuer-reports}/
- russia/dom-rf-analytics/largest-mortgage-banks-results/
- russia/rosstat/
- russia/bank-of-russia/
- russia/ministry-of-economic-development/
- russia/stock-market/{moex-exchange,spb-exchange}/

## Out of scope

Analytical work, research notes, transformed conclusions, internal methodologies, private data, and secondary-media retellings except the narrowly documented historical preservation-proxy case in Core rule 1.
