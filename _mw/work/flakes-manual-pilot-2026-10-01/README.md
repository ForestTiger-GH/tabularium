# Flakes manual pilot — 2026-10-01

Status: **temporary manual laboratory / non-authoritative**.

Purpose: test the proposed extracted-data layer on real Tabularium reports before creating a production `flakes/` contract.

The working name **flakes** is used here for the layer/package, not as a new epistemic object. Inside a flake package the record types remain explicit: source block, numeric observation, semantic assertion, candidate binding, coverage record, and finding.

The source chain remains:

`source → representation → observation/assertion → binding/derivation → analytical claim`

This laboratory stops mainly at observation/assertion and tentative binding. No record in this folder changes the evidence-layer under `scrolls/`.

## Why this pilot is intentionally manual

The goal is to discover which distinctions are actually necessary while reading reports line by line. We therefore avoid a large schema, validators, CLI, Parquet, DuckDB, or automated extraction here.

Each tested report has only:

- `manifest.json` — frozen source revision and declared pilot scope;
- `flakes.jsonl` — heterogeneous records with an explicit `record_type`.

If a later implementation benefits from splitting observations/assertions/bindings/coverage into separate files, that is a storage decision, not a semantic change.

## Reports

1. **Sber IFRS 1H 2026** — Russian consolidated IFRS statements; tests stock/flow periods, table-level units, EPS exception, and comparative columns.
2. **OTP Bank Plc. First Half 2026 Result** — currently in `_mw/_arrivals/`; tests reported vs adjusted vs normalized measures, FX-adjusted balances, management metrics, and narrative explanations.
3. **Agricultural Bank of China Q1 2026 IFRS H-share report** — tests a compact foreign IFRS report, narrative duplicates of table values, detailed loan/deposit dimensions, regulatory ratios, and an explicit PRC-GAAP metric inside an IFRS publication.

## Coverage

This first pass is deliberately **sampled**, not a claim of full-report extraction. Representative blocks are processed deeply enough to test the model. Every package contains a coverage record stating that the rest of the report is not yet processed.

The next manual pass should extend one report to complete block coverage before any production schema is accepted.
