# 📜 Tabularium

Machine-readable corpus of primary public financial, corporate, statistical, and institutional publications, plus documented bridges to canonical high-volume primary datasets.

## Route

Start from the source corpus.

- [scrolls/](scrolls/) — authoritative primary-source corpus.
  - [russia/](scrolls/russia/) — Russian public-source corpus.
  - [world/](scrolls/world/) — non-Russian and international public-source corpus.

## Corpus map

This map lists populated material classes and documented source routes.

### Russia

- [Corporate disclosures](scrolls/russia/corporate-disclosures/)
  - [Financial reporting](scrolls/russia/corporate-disclosures/financial-reporting/) — IFRS, Russian Accounting Standards reporting, and Bank of Russia regulatory bank-reporting bridges.
  - [Annual reports](scrolls/russia/corporate-disclosures/annual-reports/).
  - [Issuer reports](scrolls/russia/corporate-disclosures/issuer-reports/).
  - [Strategies](scrolls/russia/corporate-disclosures/strategies/) — standalone corporate strategy, development-plan, guidance, outlook, and forecast publications, grouped by publication year.
- [Authorities](scrolls/russia/authorities/)
  - [Bank of Russia](scrolls/russia/authorities/bank-of-russia/)
    - [Medium-Term Forecast](scrolls/russia/authorities/bank-of-russia/medium-term-forecast/).
  - [Ministry of Economic Development](scrolls/russia/authorities/ministry-of-economic-development/)
    - [Socio-Economic Development Forecast](scrolls/russia/authorities/ministry-of-economic-development/socio-economic-development-forecast/).
  - [Rosstat](scrolls/russia/authorities/rosstat/)
    - [Short-Term Economic Indicators of the Russian Federation](scrolls/russia/authorities/rosstat/short-term-economic-indicators/).
    - [Social and Economic Situation of Russia](scrolls/russia/authorities/rosstat/social-economic-position-russia/).
- [Surveys](scrolls/russia/surveys/)
  - [DOM.RF Analytics](scrolls/russia/surveys/dom-rf-analytics/)
    - [Largest Mortgage Banks Results](scrolls/russia/surveys/dom-rf-analytics/largest-mortgage-banks-results/).
  - [Moscow Exchange](scrolls/russia/surveys/moex-exchange/) — index reviews, cumulative trading-volume data, bond-market secondary trading, market-wide trading results, and retail investor activity.
  - [SPB Exchange](scrolls/russia/surveys/spb-exchange/) — trading results.

### World

- [Corporate disclosures](scrolls/world/corporate-disclosures/)
  - [Financial reporting](scrolls/world/corporate-disclosures/financial-reporting/) — non-Russian corporate financial statements and admitted financial-reporting filings, including SEC representations where applicable.
  - [Annual reports](scrolls/world/corporate-disclosures/annual-reports/) — broad annual and integrated corporate reports.
  - [Strategies](scrolls/world/corporate-disclosures/strategies/) — standalone corporate strategy, development-plan, guidance, outlook, and forecast publications, grouped by publication year.
- [Authorities](scrolls/world/authorities/) — publications from non-Russian and international public authorities, central banks, statistical agencies, regulators, and similar public bodies.
- [Surveys](scrolls/world/surveys/)
  - [Stanford](scrolls/world/surveys/usa-stanford/) — admitted public-source publications from Stanford University and its units.
  - [McKinsey](scrolls/world/surveys/usa-mckinsey/) — admitted public publications from McKinsey & Company preserved as source objects of that publisher.
  - [ICCO](scrolls/world/surveys/icco/) — primary public publications of the International Cocoa Organization.

## Scope

This repository stores source-faithful machine-readable artifacts, minimal routing metadata, and documented remote-source bridges for official high-volume datasets that are better accessed from their canonical publisher than mirrored in Git.

A bridge is a retrieval contract, not a local copy of the dataset. It must preserve primary-source identity and clearly distinguish reported values, disclosure suppression, source unavailability, and retrieval failure.

Analytical work, derived calculations, commentary, and private/internal materials belong elsewhere.

When an original primary publication is no longer publicly accessible, an explicitly documented third-party preservation proxy may be retained to preserve the historical record. Such a proxy must retain its actual provenance and must not be represented as the unavailable primary-source original.

## Data verification notice

> [!WARNING]
> Tabularium is a source-faithful research corpus and may contain transcription, extraction, parsing, conversion, or source-level errors. Do not rely on the repository as the sole source for material decisions. Verify important information against the original primary source.

## Licensing

Original Tabularium contributions are dedicated to the public domain under CC0 1.0 Universal to the extent that contributors hold the relevant rights.

Third-party source materials and source-derived content preserved or represented in this repository are excluded from that dedication and remain subject to the rights, legal status, and terms applicable to their original sources.

See [LICENSE](LICENSE) for the canonical CC0 1.0 Universal legal text and [NOTICE.md](NOTICE.md) for the scope of that dedication, treatment of third-party materials, provenance, and source-fidelity limitations.
