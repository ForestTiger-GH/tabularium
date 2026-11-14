# 📜 Tabularium

Machine-readable corpus of primary public financial, corporate, statistical, and institutional publications, plus documented bridges to canonical high-volume primary datasets.

## Route

Start from the source corpus or the source-extracted algorithm-readable layer.

- [originals/](originals/) — selectively archived, byte-for-byte original publisher files.
  - [Rosstat](originals/russia/authorities/rosstat/) — native statistical workbooks.
- [scrolls/](scrolls/) — source-faithful publications and AI-readable representations.
  - [russia/](scrolls/russia/) — Russian public-source corpus.
  - [world/](scrolls/world/) — non-Russian and international public-source corpus.
- [flakes/](flakes/) — source-extracted published observations routed by economic meaning.
  - [organizations/](flakes/organizations/) — legal entities and SMEs.
  - [banking/](flakes/banking/) — bank service networks.

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
    - [Banking Sector Dynamics](scrolls/russia/authorities/bank-of-russia/banking-sector-dynamics/) — monthly information-analytical publications on the development of Russia’s banking sector.
  - [Ministry of Economic Development](scrolls/russia/authorities/ministry-of-economic-development/)
    - [Socio-Economic Development Forecast](scrolls/russia/authorities/ministry-of-economic-development/socio-economic-development-forecast/).
  - [Rosstat](scrolls/russia/authorities/rosstat/)
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

## Native Rosstat source archives

- [Short-Term Economic Indicators](originals/russia/authorities/rosstat/short-term-economic-indicators/) — source XLSX workbooks.
- [Population of the Russian Federation by Municipalities](originals/russia/authorities/rosstat/population-by-municipality/) — native annual Rosstat population workbooks; prepared for direct uploads.

## Economic observation routes

- [Bank-by-region offices](flakes/banking/service-network/bank-regional-offices/) and [monthly territorial offices](flakes/banking/service-network/territorial-offices/) — distinct Bank of Russia source-extracted series.
- [Legal-entity population](flakes/organizations/legal-entity-population/) — FNS Form 1-YUR registered legal entities.
- [SME register population](flakes/organizations/sme-register-population/) — FNS legal-entity and entrepreneur regional counts.

## Scope

This repository selectively archives untouched publisher artifacts under `originals/`, preserves source-faithful AI-readable publications under `scrolls/`, and stores algorithm-readable, source-traceable, series-specific records under `flakes/`, along with minimal routing metadata and documented remote-source bridges for official high-volume datasets. The stages are optional rather than a mandatory chain. An integrated cross-series database and downstream marts or visualizations can operate outside Tabularium.

A bridge is a retrieval contract, not a local copy of the dataset. It must preserve primary-source identity and clearly distinguish reported values, disclosure suppression, source unavailability, and retrieval failure.

`flakes/` preserves programmatically usable series with source values and semantics; structures may differ markedly between series, and common names do not guarantee harmonized observations. A source does not require an archived `originals/` or `scrolls/` copy before being captured into `flakes/`. Operational monitoring and source-local analytical alerts may use flakes directly; derived results must remain distinguishable from source evidence. General cross-series analytics, integrated marts, and visualizations belong to downstream systems.

When an original primary publication is no longer publicly accessible, an explicitly documented third-party preservation proxy may be retained to preserve the historical record. Such a proxy must retain its actual provenance and must not be represented as the unavailable primary-source original.

## Data verification notice

> [!WARNING]
> Tabularium is a source-faithful research corpus and may contain transcription, extraction, parsing, conversion, or source-level errors. Do not rely on the repository as the sole source for material decisions. Verify important information against the original primary source.

## Licensing

Original Tabularium contributions are dedicated to the public domain under CC0 1.0 Universal to the extent that contributors hold the relevant rights.

Third-party source materials and source-derived content preserved or represented in this repository are excluded from that dedication and remain subject to the rights, legal status, and terms applicable to their original sources.

See [LICENSE](LICENSE) for the canonical CC0 1.0 Universal legal text and [NOTICE.md](NOTICE.md) for the scope of that dedication, treatment of third-party materials, provenance, and source-fidelity limitations.
