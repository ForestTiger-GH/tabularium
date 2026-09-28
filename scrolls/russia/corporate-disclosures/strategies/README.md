# Strategies

Standalone primary corporate strategy and forward-looking publications issued by Russian corporate entities and groups.

## Scope

This route is for source publications whose principal purpose is to communicate future corporate direction, targets, plans, expectations, or forecasts, including:

- formal corporate strategies and development programs;
- standalone strategic plans and strategy-day or capital-markets-day materials centered on strategic priorities and targets;
- standalone official guidance, outlook, target, or forecast publications.

Do not duplicate an annual report, issuer report, financial statement, or other artifact here merely because it contains strategy discussion or forward-looking statements. One primary material is stored physically once in its primary publication class.

## Year routing

Store artifacts under:

- [2026/](2026/)
- [2025/](2025/)
- [2024/](2024/)

The directory year is the year in which the source was publicly published or released. It is not the strategy horizon, forecast target year, reporting period, or an analytical reference year.

Use a publication year only when it is supported by the source or its primary publication context. Do not infer a publication date from a target horizon, approval date, covered period, or filename.

A later reissue or revised version is a distinct source representation when the publisher releases it as such; preserve its actual release date and version relationship rather than silently replacing the earlier source.

## Artifact identity

Prefer a source-supported publication date in ISO form when available. A useful identity pattern is:

```text
<ENTITY>_<PUBLICATION-DATE>_<DOCUMENT-KIND>[_<VARIANT>].<ext>
```

Do not invent missing day or month precision. The strategy horizon belongs to provenance or observation metadata when explicitly stated by the source; it is not a substitute for the publication date.

## Source fidelity

Forward-looking targets, scenarios, plans, guidance, and forecasts are reported source statements. Their inclusion in Tabularium does not assert that they are achievable, probable, internally consistent, or subsequently realized.

Preserve source wording, scope, units, horizon, assumptions, version, and provenance. Keep related artifacts from one release together under the repository publication-unit rules. Derived forecasts, normalized targets, promise tracking, success/failure assessments, and other analytical conclusions belong above the source layer.
