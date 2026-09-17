# AGENTS.md

## Repository purpose

`tabularium` is a public, source-faithful corpus of machine-readable primary publications.

## Core rules

1. Store primary public-source artifacts only.
2. Preserve source meaning and reported values. Do not add analysis, interpretation, normalization, derived calculations, or private/internal data.
3. Route artifacts by country first, then by publication family and reporting regime.
4. Do not classify entities by industry in the physical directory tree unless the repository contract is explicitly revised.
5. Keep paths and repository control files in English, lowercase, and ASCII where practical.
6. Each directory must contain a minimal `README.md` that explains only its purpose and onward routes.
7. Add new top-level taxonomies only when a real source class requires them. Avoid speculative empty structure.

## Current route

`russia/financial-reporting/{ifrs,ras}/`

## Out of scope

Analytical work, research notes, transformed conclusions, internal methodologies, private data, and secondary-media retellings.
