# AGENTS.md

## Scope

These instructions apply to the Bank of Russia regulatory reporting bridges under this directory.

## Source authority

Use official Bank of Russia sources as the canonical source for forms 0409101, 0409102, 0409123, and 0409135.

Do not treat local bridge metadata as the financial data itself.

## Entity resolution

Before retrieving a form, resolve the credit institution against a live Bank of Russia source.

Keep distinct:
- OGRN, used by the Bank of Russia institution reporting index;
- Bank of Russia registration number, used by form and web-service interfaces;
- the institution's current and historical names.

Do not infer identity from a short bank name when the official identifier can be resolved.

## Retrieval order

1. Use the Bank of Russia institution reporting page to verify that the form and requested date are available:
   https://www.cbr.ru/finorg/foinfo/reports/?ogrn={ogrn}
2. Prefer the official human-readable HTML presentation when it exposes the requested main data.
3. If the request needs deeper detail, a time series, metadata, or a row not exposed in the HTML presentation, use the CreditOrgInfo SOAP web service documented in the form bridge.
4. If needed and the runtime can process binary archives, use the official Bank of Russia bulk DBF archive and the date-effective format description.
5. If the requested detail is suppressed by the applicable public-disclosure regime, do not reconstruct it from aggregates. An exact official disclosure by the credit institution itself may be used only as a separate primary source with its own provenance.

## Disclosure regime

Disclosure is date-sensitive. Before treating an absent account, symbol, row, field, or ratio as unavailable, check the Bank of Russia disclosure decision applicable to that reporting date.

For 2026, the Bank of Russia decision dated 19 December 2025 limits public disclosure of all four forms:
https://www.cbr.ru/rbr/dir_decisions/rsd_2025-12-19_23_02/

Do not extrapolate the 2026 rules backward or forward. Historical periods may have different public granularity.

## Result states

Use these semantic states when a requested observation cannot be returned directly:

- reported — the value is explicitly published by the primary source;
- suppressed — the item exists conceptually but public disclosure for the date does not expose it at the requested granularity;
- not_available — the relevant form or reporting date is absent from the public source;
- retrieval_failed — the source should exist, but the current runtime could not retrieve or parse it.

Never convert suppressed, not_available, or retrieval_failed into zero.

## Source fidelity

Preserve source codes, labels, account side, row identifiers, symbols, dates, period boundaries, units, and reported values.

Keep identifier-like codes as strings when leading zeroes, punctuation, or Cyrillic characters are meaningful.

Derived calculations belong in analytical work outside this source layer. When a calculation is requested, cite the source observations separately from the derived result.
