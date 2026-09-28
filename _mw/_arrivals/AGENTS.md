# AGENTS.md

## Scope

These instructions apply to all files placed under `_mw/_arrivals/`.

This directory is a temporary intake queue. It is outside the authoritative source corpus under `scrolls/`. An arrival becomes a corpus artifact only after it has been inspected, correctly identified, processed under the applicable source-faithful rules, and placed in its final route.

## Processing protocol

When the user asks to process arrivals:

1. **Inventory before changing anything.** Identify the files to be processed and do not infer source identity from an arbitrary intake filename.
2. **Inspect the source.** Establish, from the source itself or its primary publication context where available, the publisher/reporting entity, entity jurisdiction where relevant, publication class, reporting period or date, reporting perimeter, accounting framework when explicitly determinable, publication variant, language, and source format.
3. **Use the current repository contract.** Read the root `AGENTS.md` and the README/AGENTS files governing the candidate target route before naming, converting, moving, or creating anything.
4. **Prefer an existing route.** Do not invent a new taxonomy when an established source class fits. Create a new route only when a real source class materially requires it and update the routing contract minimally.
5. **Name from source-supported facts only.** Follow the target route's filename convention. Never guess a period, jurisdiction, framework, filing type, perimeter, or variant merely to complete a filename.
6. **Preserve source fidelity.** Do not correct, normalize, reinterpret, combine, or silently enrich source content. Keep natively machine-readable source artifacts in their original format where required by the repository contract. Convert PDF publications to complete source-faithful Markdown representations under the current corpus rules.
7. **Keep publication units intact.** If one release contains multiple related artifacts, preserve the release as one atomic unit and follow the root rules for issue directories.
8. **Protect existing corpus artifacts.** Before writing a destination path, check for an existing artifact with the same apparent identity. Do not overwrite or merge it until the source/version relationship is established.
9. **Verify before cleanup.** Confirm that the final artifact exists at the intended path, has the intended name and representation, and has not lost source content before removing the intake copy.
10. **Do not leave successful duplicates.** After verified admission to `scrolls/`, remove the corresponding file from `_mw/_arrivals/` unless the user explicitly requires the intake copy to remain.
11. **Do not manufacture certainty.** If a material routing or identity fact remains unresolved, keep the file in arrivals and report the blocker. Missing or unknown information is not a license to infer it.

## Naming notes

For Russian corpus routes, use the naming contract documented by the applicable `scrolls/russia/` route.

For non-Russian corporate publications under `scrolls/world/corporate-disclosures/`, follow `scrolls/world/README.md`, including the reporting-entity jurisdiction prefix and actual reporting-period end date where applicable. For source-institution routes under `scrolls/world/`, follow the target route README and preserve the publisher, series, edition/date, version, and provenance supported by the source.

The filename is an identity aid, not a substitute for source provenance. A successful move must preserve the distinction between source, representation, observation, derivation/bridge, and analytical claim.
