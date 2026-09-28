# World

Primary machine-readable public-source publications outside the Russian route.

## Route

- [corporate-disclosures/](corporate-disclosures/) — non-Russian corporate financial reporting, annual-report, and standalone strategy or forward-looking publications.
- [usa-stanford/](usa-stanford/) — admitted public-source publications from Stanford University and its units.
- [usa-mckinsey/](usa-mckinsey/) — admitted public publications from McKinsey & Company preserved as source objects of that publisher.
- [icco/](icco/) — primary public publications of the International Cocoa Organization.

Corporate disclosures are routed by publication class. Institution routes are used only where the publisher or institution is itself a durable source axis. Do not duplicate one source artifact across routes.

## Financial and annual-report artifact identity

For artifacts under `corporate-disclosures/financial-reporting/` and `corporate-disclosures/annual-reports/`, filenames should expose only the small set of source-identity fields useful for stable routing and human inspection. Richer attributes belong in registry metadata rather than in deeper directory trees.

Artifacts under `corporate-disclosures/strategies/` use publication-date identity instead; follow that route's README. A strategy horizon or target year must never substitute for the source publication date.

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

Do not invent a day or period boundary that the source does not support.

### Publication type

`<PUBLICATION-TYPE>` describes the primary publication or filing class, not the accounting framework. Use a short, source-recognizable token such as `ANNUAL`, `INTERIM`, `10-K`, or `20-F`.

### Accounting framework

`<ACCOUNTING-FRAMEWORK>` is optional. Include it only when the source supports an unambiguous framework classification useful for distinguishing the representation, for example `IFRS`, `EU-IFRS`, `US-GAAP`, `PRC-ASBE`, or `HKFRS`.

Do not force a single framework token onto a publication containing multiple accounting representations.

### Variant

`<VARIANT>` is optional and should be used only when a source-level distinction is needed to distinguish otherwise colliding publications or representations. Do not use variants to encode analytical classifications.

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

SEC is a filing channel, not a separate physical source route for these corporate financial-reporting artifacts. An admitted SEC filing is stored once under `corporate-disclosures/financial-reporting/`.

Do not create country, industry, or accounting-framework subdirectories inside `corporate-disclosures/` unless a real source class and an explicit repository-contract change require them. Source-institution routes may add stable publication-series subdirectories only when actual admitted publications require them. Preserve all source-fidelity, provenance, format, and publication-unit rules from the repository root.
