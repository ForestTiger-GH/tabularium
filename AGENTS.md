# AGENTS.md

## Repository purpose

`tabularium` is a public, source-faithful corpus of machine-readable primary publications.

## Core rules

1. Store primary public-source artifacts only.
2. Preserve source meaning and reported values. Do not add analysis, interpretation, normalization, derived calculations, or private/internal data.
3. Route by country first. Within a country, use stable source routes documented by that country. Financial reporting remains under its dedicated reporting family; recurring official publications may route by source institution and stable publication series.
4. Do not classify entities or publications by industry or topic in the physical directory tree unless the repository contract is explicitly revised.
5. Keep paths and repository control files in English, lowercase, and ASCII where practical.
6. Routing directories and stable publication-series directories must contain a minimal `README.md`. Period/issue directories do not require one.
7. Keep natively machine-readable source artifacts such as XLSX, CSV, XML, and JSON in their original format. Store PDF publications as complete source-faithful Markdown transcriptions.
8. Keep all artifacts belonging to the same publication issue or release together. A single-artifact issue may remain a period/date-named file; create an issue directory when a release contains multiple related artifacts.
9. Add new top-level taxonomies only when a real source class requires them. Avoid speculative empty structure.

## Current routes

- `russia/financial-reporting/{ifrs,ras}/`
- `russia/rosstat/`
- `russia/bank-of-russia/`
- `russia/ministry-of-economic-development/`

## Out of scope

Analytical work, research notes, transformed conclusions, internal methodologies, private data, and secondary-media retellings.
