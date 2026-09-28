# World

Primary machine-readable corporate publications from reporting entities outside the Russian Federation.

## Route

- [financial-reporting/](financial-reporting/) — general-purpose annual, interim, and quarterly financial reporting and closely related statutory or regulatory financial filings whose principal evidentiary value is the financial statements.
- [annual-reports/](annual-reports/) — broad annual or integrated corporate reports published as a distinct primary publication class.

## Artifact identity

Use the reporting entity's ISO 3166-1 alpha-2 jurisdiction code as the filename prefix. The prefix identifies the reporting entity, not the exchange, filing regulator, accounting framework, language, or principal market.

Use the actual reporting-period end date in ISO form `YYYY-MM-DD` where applicable.

Preferred pattern:

```text
<CC>_<ENTITY>_<PERIOD-END>_<PUBLICATION-TYPE>[_<ACCOUNTING-FRAMEWORK>][_<VARIANT>].<ext>
```

Include an accounting-framework token only when the source supports an unambiguous classification. Do not force a single framework onto a publication containing multiple accounting representations.

Do not create country, industry, or accounting-framework subdirectories here unless a real source class and an explicit repository-contract change require them. Preserve all source-fidelity, provenance, format, and publication-unit rules from the repository root.
