# Arrivals

`_mw/_arrivals/` is the temporary intake area for newly added source files that have not yet been admitted to the authoritative Tabularium corpus.

Files here may arrive with arbitrary or incomplete names. Their presence in this directory does **not** establish final source identity, route, period, accounting framework, reporting perimeter, or publication type, and they must not be treated as authoritative corpus artifacts while they remain here.

## Intended workflow

When processing arrivals:

1. inspect the source itself and establish its provenance and publication identity;
2. determine the applicable existing route under `scrolls/`;
3. read the repository root rules and the target route's README/AGENTS instructions;
4. assign the filename required by the target route from source-supported facts only;
5. preserve or convert the artifact according to the repository format rules;
6. place the completed artifact in its final corpus location;
7. verify the final artifact and path;
8. remove the successfully processed intake copy from `_arrivals/`.

Do not create country, industry, accounting-framework, or other new physical taxonomies merely to accommodate an arrival. Introduce a new route only when a real source class requires it under the repository contract.

If a source cannot be identified or routed without guessing a material fact, leave it in `_arrivals/` and report the unresolved point rather than inventing metadata.

This directory is staging, not a permanent archive and not part of the evidence-layer.
