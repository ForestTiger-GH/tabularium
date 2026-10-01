# Flakes manual pilot — 2026-10-01

Status: **temporary manual laboratory / non-authoritative**.

Purpose: test the proposed extracted-data layer on real Tabularium reports before creating a production `flakes/` contract.

The working name **flakes** is used here for the layer/package, not as a new epistemic object. Inside a flake package the record types remain explicit: source block, numeric observation, semantic assertion, candidate binding, validation check, coverage record, and finding.

The source chain remains:

`source → representation → observation/assertion → binding/derivation → analytical claim`

No record in this folder changes the evidence-layer under `scrolls/`.

## Why this pilot is intentionally manual

The goal is to discover which distinctions are actually necessary while reading reports line by line. We therefore avoid a production schema, CLI, database, Parquet/DuckDB layer, or automated corpus-wide extraction.

Each tested report has only:

- `manifest.json` — frozen source revision and declared pilot scope/profile;
- `flakes.jsonl` — heterogeneous records with an explicit `record_type`.

If a later implementation benefits from splitting observations/assertions/bindings/coverage/checks into separate files, that is a storage decision, not a semantic change.

## Reports

1. **Sber IFRS 1H 2026** — sampled pages 5–6. Tests stock/flow periods, statement units, EPS exception, comparative columns, source subtotals and balance identities.
2. **OTP Bank Plc. First Half 2026 Result** — sampled pages 2, 4 and 5; source is still in `_mw/_arrivals/`. Tests reported vs adjusted vs normalized measures, FX-adjusted balances, management ratios, narrative methodology and source rounding.
3. **Agricultural Bank of China Q1 2026 IFRS H-share report** — complete page-by-page pass under the explicit `financial_core_v0` profile. Tests source duplicates, detailed dimensions, regulatory ratios, PRC-GAAP overrides inside an IFRS publication, hierarchical statement rows, source dashes, unlabeled subtotals, residual bridges and cash-flow identities.

## Current coverage status

- Sber: **sampled**, 2 source blocks.
- OTP: **sampled**, 3 source blocks.
- ABC: **processed_complete_for_profile** across all 16 pages. Detailed shareholder-register positions and identifier/contact numbers are explicitly excluded by `financial_core_v0`, rather than silently ignored.

“Complete for profile” is intentionally different from “every number in the document was extracted”.

See `STATUS.md` for record counts and `FINDINGS.md` for architectural lessons.
