# Pilot status

Date: 2026-10-01. Status: temporary manual laboratory.

| Package | Scope | Blocks | Observations | Assertions | Proposed bindings | Checks | Findings | Coverage |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Sber IFRS 1H 2026 | Pages 5–6, selected rows | 2 | 24 | 1 | 4 | 4 | 1 | sampled |
| OTP Bank Plc. 1H 2026 Result | Pages 2, 4–5 | 3 | 20 | 4 | 4 | 7 | 2 | sampled |
| Agricultural Bank of China Q1 2026 IFRS H-share | All 16 pages under `financial_core_v0` | 17 | 326 | 5 | 4 | 18 | 8 | processed_complete_for_profile |

## Integrity

- All three `flakes.jsonl` files parse as JSONL.
- No duplicate record IDs were detected in the checked identity fields.
- All checked `binding → observation`, `record → block`, `check → input observation/assertion`, and `coverage → block` references resolve.
- Source files under `scrolls/` were not modified.
- OTP remains an arrival-staging source; its package is pinned to Git blob `d7cbd5519fa95e41843ece8b80e74df8ac2493ab`.

## What this pilot has actually established

It has **not** established a production schema.

It has established that real reports require, at minimum, explicit handling of:

- source revision;
- block/page structure;
- literal vs parsed value;
- period/grain;
- row-level unit/basis overrides;
- reported vs adjusted/normalized roles;
- source dimensions;
- hierarchy/subtotals;
- non-numeric states such as `–`;
- semantic assertions;
- tentative bindings independent of extraction;
- coverage profile;
- validation checks;
- findings/unresolved semantics;
- multiple evidence occurrences and later selection policy.

The next useful manual extension is not more schema work. It is to take a second report with a different failure mode to full profile coverage—preferably OTP, because its adjusted/normalized methodology is much harder than ABC’s compact IFRS statements.
