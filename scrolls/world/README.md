# World

Primary machine-readable corporate publications from reporting entities outside the Russian Federation.

## Route

- [financial-reporting/](financial-reporting/) — general-purpose annual, interim, and quarterly financial reporting and closely related statutory or regulatory financial filings whose principal evidentiary value is the financial statements.
- [annual-reports/](annual-reports/) — broad annual or integrated corporate reports published as a distinct primary publication class.

## Artifact identity

World-corpus filenames should expose only the small set of source-identity fields that are useful for stable routing and human inspection. Richer attributes belong in registry metadata rather than in deeper directory trees.

Preferred pattern:

```text
<CC>_<ENTITY>_<PERIOD-END>_<PUBLICATION-TYPE>[_<ACCOUNTING-FRAMEWORK>][_<VARIANT>].<ext>
```

Use underscores to separate identity fields and hyphens inside a field where needed. Keep the name concise: a filename is an identity aid, not a complete metadata record.

### Country prefix

`<CC>` is the reporting entity's ISO 3166-1 alpha-2 jurisdiction code.

It identifies the reporting entity, not the exchange, filing regulator, accounting framework, language, or principal market. A British issuer filing a Form 20-F with the SEC therefore remains `GB_...`; a Chinese issuer publishing an H-share report remains `CN_...`.

### Entity

`<ENTITY>` is a stable repository name for the reporting entity or group, not its stock ticker.

Use a concise ASCII form where practical and use hyphens inside multi-word names. Do not collapse a legal entity and a consolidated group merely because their names are similar; reporting perimeter remains part of source identity.

Examples:

```text
US_NVIDIA
NL_RABOBANK
GB_SHELL
CN_AGRICULTURAL-BANK-OF-CHINA
```

### Reporting-period end

`<PERIOD-END>` is the actual end date of the reporting period, preferably in ISO form `YYYY-MM-DD`.

Use the reporting-period end rather than the filing date, publication date, or fiscal-year label. This matters for issuers whose fiscal years do not end on a calendar month-end.

For example, a fiscal 2026 report for a period ending 25 January 2026 uses:

```text
2026-01-25
```

Do not invent a day or period boundary that the source does not support.

### Publication type

`<PUBLICATION-TYPE>` describes the primary publication or filing class, not the accounting framework.

Use a short, source-recognizable token such as:

```text
ANNUAL
INTERIM
10-K
20-F
```

A Form 10-K prepared under US GAAP therefore carries both concepts separately: `10-K` is the filing type; `US-GAAP` is the accounting framework.

### Accounting framework

`<ACCOUNTING-FRAMEWORK>` is optional.

Include it only when the source supports an unambiguous framework classification that is useful for distinguishing the representation, for example:

```text
IFRS
EU-IFRS
US-GAAP
PRC-ASBE
HKFRS
```

Do not force a single framework token onto a publication containing multiple accounting representations. In that case, omit the token from the filename and preserve the framework distinctions in the source representation and registry metadata.

### Variant

`<VARIANT>` is optional and should be used only when a source-level distinction is needed to distinguish otherwise colliding publications or representations.

Examples include A-share versus H-share versions or another publisher-defined filing variant. Do not use variants to encode analytical classifications.

## Examples

```text
US_NVIDIA_2026-01-25_10-K_US-GAAP.html
US_CISCO_2025-07-26_10-K_US-GAAP.html
NL_RABOBANK_2026-06-30_INTERIM_EU-IFRS.md
NL_RABOBANK_2025-12-31_ANNUAL.md
CN_AGRICULTURAL-BANK-OF-CHINA_2025-12-31_ANNUAL_PRC-ASBE_ASHARE.md
CN_AGRICULTURAL-BANK-OF-CHINA_2025-12-31_ANNUAL_IFRS_HSHARE.md
GB_SHELL_2025-12-31_20-F_IFRS.html
GB_SHELL_2025-12-31_ANNUAL.md
```

These examples illustrate the intended separation of dimensions:

- the country prefix identifies the reporting entity's jurisdiction;
- the period token preserves the actual reporting-period boundary;
- the publication token identifies what the source publication is;
- the accounting-framework token identifies how the financial statements are represented when that classification is unambiguous;
- the optional variant distinguishes parallel source versions without creating another directory level.

This keeps `scrolls/world/` physically flat while preserving enough identity in each filename for reliable intake, routing, registry generation, and later provenance checks.

Do not create country, industry, or accounting-framework subdirectories here unless a real source class and an explicit repository-contract change require them. Preserve all source-fidelity, provenance, format, and publication-unit rules from the repository root.
