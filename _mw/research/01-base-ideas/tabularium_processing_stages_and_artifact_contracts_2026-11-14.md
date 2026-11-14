# Tabularium: Processing Stages, Artifact Roles, and the Boundary of the Integrated Data Layer

**Status:** Architecture research and proposed conceptual model; not an adopted repository contract or a migration instruction.  
**Date:** 2026-11-14  
**Scope:** Tabularium's evidence corpus and the wider processing ecosystem, including downstream systems that may live outside the repository.

## Core conclusion

The sequence **originals → scrolls → flakes → integrated database → output views and products** describes increasing *processing readiness and integration scope*, not a mandatory chain through which every publication must pass. Each stage answers a different practical question:

1. **Originals:** What exact file did the publisher distribute?
2. **Scrolls:** How can the publication be read and understood faithfully by an AI consumer?
3. **Flakes:** How can the publication's data or assertions be consumed predictably by algorithms within a particular series?
4. **Integrated database:** How can heterogeneous series enter one governed, queryable data environment without losing their original semantics?
5. **Views and products:** How can integrated data be selected, compared where justified, calculated, presented, and delivered?

The stages are **not** a ranking of truth, a progression from unstructured to numeric data, or an assertion that an identical economic indicator exists across every source. In particular, **`flakes/` is an algorithm-readable corpus with series-local structure, not a universally harmonized dataset**. Series may be internally consistent and still be fundamentally incompatible with other series. The database is a downstream integration stage, potentially outside Tabularium. Monitoring and narrowly scoped analytical notifications can operate earlier, including directly from flakes.

This model proposes an optional root **`originals/`** archive for retained untouched publisher files. Its source-oriented routes should mirror existing `scrolls/` routes where both exist. Whether an original is retained is a source-specific decision: preservation is valuable for selected statistical workbooks, but may be disproportionate for large financial-reporting PDFs that already have faithful representations and resolvable external sources. No conversion or duplicate archival step is required solely to satisfy the conceptual diagram.

### Reading guide

- Sections 1–3 define the processing distinction and each artifact stage.
- Sections 4–5 establish the integrated database and downstream-output boundary.
- Sections 6–7 describe optional paths, provenance, and semantics.
- Sections 8–9 cover early notifications, ecosystem ownership, and practical examples.
- Sections 10–11 propose an incremental Tabularium transition and testable design criteria.

## 1. Processing readiness is the organizing dimension

### 1.1. Five questions, five responsibilities

| Stage | Primary responsibility | Readiness established | What is *not* promised |
| --- | --- | --- | --- |
| `originals/` | Preserve a selected publisher file as originally distributed | Exact-byte historical recovery and native-source inspection | AI-friendly reading, algorithm-ready tables, or cross-source compatibility |
| `scrolls/` | Preserve a faithful, AI-readable publication or representation | AI can consume the source content, structure, narrative, and context | Stable series-level schemas, regular extraction, or harmonized metrics |
| `flakes/` | Preserve algorithm-consumable, source-traceable series artifacts | Programs can reliably address records and fields according to a **series-specific** contract | One global layout, uniform indicator taxonomy, or economic comparability across series |
| Integrated database | Ingest and integrate heterogeneous data into a common governed storage/query contour | Cross-series discovery, common addressing, typed storage, explicit identity and relationships | Automatic conceptual equivalence or a license to alter reported values |
| Views, marts, products | Build outputs from the integrated data environment | Reusable tables, charts, reporting outputs, services, applications, and analytical results | Independent authority over the original evidence |

These are **roles**, not exclusive file extensions. An XLSX is technically machine-readable; nevertheless, a complex untouched Rosstat workbook can belong to `originals/` because it has not been transformed into a predictable series-specific extraction contract. Conversely, a source CSV may already be suitable for direct algorithmic use. HTML may be both source-native and AI-readable, allowing direct admission to `scrolls/`.

### 1.2. Different meanings of readability

Three concepts must not be conflated:

- **Native machine readability:** A program can technically parse a format such as XLSX, HTML, JSON, XML, or CSV. This says little about semantic consistency or the amount of custom extraction code required.
- **AI readability:** An AI consumer can inspect the publication's meaningful content, labels, narrative, tables, caveats, and structure with adequate fidelity. It may use HTML, Markdown, or another appropriate representation. It does not imply every record has a stable algorithmic address.
- **Algorithmic, series-contract readability:** A program can load and process records using a documented, reasonably predictable contract for the particular series. This is the central promise of `flakes/`.

A fourth, separate property is **cross-series integration readiness**: disparate records can be incorporated into a common data model and queried in one environment. This belongs to the integrated database, not to every flake.

These properties can coexist in one native format, but the repository should determine placement by **artifact responsibility and actual processing state**, not extension alone.

### 1.3. The route is logical, not compulsory

The full conceptual route is:

```text
publisher / external source
          |
          +----> originals ----> scrolls ----> flakes ----> integrated database ----> views / marts / products
          |           |                          ^
          |           +--------------------------+
          |
          +-----------------> scrolls -----------+
          |
          +-------------------------------------> flakes
```

Any intermediate stage can be skipped when its function is unnecessary. Some publications stop at `originals/`, some at `scrolls/`, and some at `flakes/`. The database is not required to exist inside the GitHub repository. Where a data product is meant to be a unified analytical output, its expected canonical route begins at the integrated database even if an operational alert was produced earlier.

## 2. `originals/`: selected, untouched publisher artifacts

### 2.1. Exact responsibility

`originals/` contains **selected original publisher-distributed files**, preserved without changing their bytes. Permissible repository-side actions include selecting the artifact for preservation, placing it on an appropriate source route, and renaming the file according to a documented naming rule. Changing the filename must not mutate the contents.

Do not edit workbook cells or metadata, remove sheets, normalize formulas, convert character encodings, rewrite archives, reconstruct an XLSX from parsed values, or repackage a PDF and label the result as the original. Extracted or converted artifacts have their own identity and belong to subsequent stages.

The archive is **selective**, not a rule that every external download be stored twice.

### 2.2. Why some sources merit original-byte retention

Preservation is especially useful when the original file structure is indispensable to later inspection: complex Rosstat statistical workbooks, source-specific formatting, footnotes, formula cells, merged regions, embedded classifications, workbook revisions, and multi-sheet presentations. For demographic, population, labor, and other statistical series, the untouched workbook can be the decisive reference when extraction code is revised.

Large IFRS publications present a different cost/benefit profile. If copying all publisher PDFs would make the public Git repository disproportionately heavy, the source may be read transiently, retained as a faithful `scrolls/` representation when appropriate, and identified through its publication location and retrieval evidence rather than mirrored in `originals/`. The absence of a local original must not be hidden: a faithful representation is not an assertion that the source bytes are locally recoverable.

Other high-volume official datasets may justify a documented remote-source retrieval bridge rather than a local binary mirror when the publisher provides suitable durable access.

### 2.3. Mirrored source routing, not mirrored file inventories

The proposed root route is `originals/`. Where useful, its internal source hierarchy mirrors `scrolls/`:

```text
originals/
  russia/
    authorities/
      rosstat/
        short-term-economic-indicators/
          2026-07.xlsx
        <populated-population-publication-series>/
          ...
  world/
    ...
```

The country, institution, publication class, and stable series route have the same meaning in both trees. **Do not create an empty counterpart for every scroll route.** Only preserve actual accepted originals and add a stable series directory when justified by a real source. A sufficiently frequent monthly series may be divided into calendar-year directories if this improves maintenance.

All artifacts belonging to one publication issue are one logical release; multiple source files can reside together in an issue directory. A publisher ZIP remains a publisher ZIP when the objective is exact-byte preservation; extracted members are not silently substituted for the original archive.

### 2.4. Identity, versions, and file integrity

Keep publisher identity, series, release/reference date, source URL or publication locator when available, and a verifiable byte hash when needed for updates and lineage. Distinguish publication date, statistical reference period, retrieval date, and correction/version date.

If a publisher silently replaces the binary file for a previously published period, the new bytes are a revised source state. History or a release-event record must permit the prior state to be distinguished; a replacement must not erase the ability to understand which version fed a downstream extraction. Hashes establish byte identity, not correctness of the published figures.

No obligatory manifest per workbook is implied. Reuse minimal existing route documentation, Git history, and source-specific event logs where they are adequate.

## 3. `scrolls/` and `flakes/`: distinct processing functions

### 3.1. `scrolls/` is AI-readable source content

`scrolls/` holds source-faithful content rendered in a form convenient for AI reading and reasoning over the *publication as a publication*. This includes text, tables, notes, context, labels, caveats, and the narrative needed to interpret what the publisher actually asserted.

Examples include a complete faithful Markdown transcription of a PDF and a source HTML page that is already sufficiently readable as captured. A native source may therefore enter `scrolls/` **directly**. There is no reason to make an identical, unused `originals/` copy merely because a capture step occurred.

A scroll is not required to present every statistic as a regular rectangular row set. It may preserve complex document hierarchy, narrative, and irregular table layout better than a flat extraction. It must not silently introduce interpretation, adjustments, corrected values, or an invented methodological equivalence.

A scroll can exist without an archived original; if it is a transformation of an unretained source, its origin and representation status should remain knowable. When the same issue is archived in `originals/`, the scroll can point back to that version without duplicating the bytes.

### 3.2. `flakes/` is the algorithm-readable corpus, not the universal database

`flakes/` stores records and machine-operable assertions that algorithms can address and use under **local contracts for stable source series**. Numerical and semantic material may both qualify.

A typical flake series might provide a CSV with the same record grain and a documented set of columns across releases. Another series might be JSON or another suitable machine-consumable representation with a wholly different field structure. This is legitimate: algorithmic usability does not require all flake artifacts to look alike.

**Series-local alignment** means that, where the source permits, a script can recognize an observation's place within the same publication series over time. It does not require identical columns across all historical editions. Methodological breaks, changed territorial perimeters, superseded category dictionaries, unavailable fields, and other genuine source changes remain observable. An edition-aware adapter can expose version-qualified mappings without pretending a non-equivalent old field is the same construct.

**Cross-series non-uniformity** is expected. A regional population table, an FNS legal-entity table, a bank-by-region office table, and a corporate financial statement can have radically different record grains, periods, units, classification systems, and layouts, even though each is algorithm-friendly.

The practical `flakes/` contract is:

- stable, explicit meaning **within each individual series or edition**, as far as the source supports it;
- traceable source identity, values, labels, periods, categories, and limitations;
- machine-consumable organization sufficient for repeatable series-specific extraction, comparison, checking, and scripts;
- no implicit claim that two different series have equivalent fields merely because column names are similar;
- no requirement for one repo-wide table schema, universal long format, canonical unit, or database-specific record structure.

`flakes/` may contain source-extracted **representations**, not merely single scalar observations. A table containing multiple source columns is a legitimate flake if it can be handled reliably by a program. Its existence is not proof that it has been globally normalized.

### 3.3. Extraction is a semantic operation, not just parsing

Constructing a flake from an original or scroll can involve selecting a table, identifying header layers, retaining source units, resolving period labels, exposing cell positions, and recording classifications. These operations must be reproducible and must not silently change economic meaning.

A structurally reoriented source table can be acceptable if the original observations and their meanings remain reconstructible. A renamed field is acceptable only when its source-specific identity is documented. The transformation must not invent values, replace missing observations with zero, silently suppress rows, or join time series across classification breaks without an explicit bridge.

The distinction is crucial: **machine-ready is not the same as analytically adjusted**.

### 3.4. Direct acquisition into flakes is allowed

Some publications are fetched only transiently from a public endpoint, parsed, and saved directly as repeatable series-level CSV records. This does not require an archived `originals/` artifact or a fabricated `scrolls/` file. Source capture rules, retrieval evidence, event records, and conversion provenance must remain sufficient for the series' actual risk and reproducibility requirements.

An original-to-flake transformation and a scroll-to-flake transformation are both legitimate. A flake is neither logically nor physically required to derive from a scroll when a more faithful direct extraction exists.

## 4. Integrated database: one contour without false economic equivalence

### 4.1. What complete integration means

The integrated database is the place where heterogeneous flake series are **brought into one addressable and queryable storage environment**. It has cross-source ingestion and storage conventions: common record identity, typed fields, period and version handling, publisher and subject references, provenance, source statuses, and explicit relationships among series.

This is a greater level of integration than `flakes/`. A program querying the database should not have to know where every CSV file is stored or maintain an ad hoc parser for each publisher's release structure. Source-specific import adapters establish a unified query contour.

The database can hold an integrated long-form observation grid, multiple related tables, source-native side structures, or another justified physical organization. A universal long table is a useful projection, **not an obligation to flatten away source semantics**.

### 4.2. Common storage is not common meaning

Two observations may share a display label such as `population`, `assets`, `office count`, or `profit` and still differ in population definition, consolidation perimeter, unit, accounting basis, geography, period, classification edition, or published status.

Therefore:

- a common database column or construct label does not establish comparability;
- source-specific identity and publication edition remain distinct from a proposed canonical construct;
- mappings can be **identity mappings**, **qualified correspondences**, **explicit derivations**, or **unsupported/unknown**;
- transformations such as currency conversion, deflation, seasonal adjustment, entity consolidation, territory reconciliation, and growth calculations require declared operations and input references;
- where no reliable bridge exists, both series can coexist in the database without being combined into one analytical sequence.

In other words, the database is **fully integrated as a managed data environment**, not falsely harmonized as an economic ontology. Source meaning must survive the integration.

### 4.3. Minimum conceptual identity of a record

A useful cross-series envelope should be able to resolve, when relevant and known:

```text
publisher / source series / publication issue / source version
source artifact or representation locator
reporting entity or statistical subject
source construct and edition-qualified classification
observation or reference period / capture date
geographic and organizational perimeter
reported unit / scaling / literal value / value type
reported status and source qualification
extraction or mapping method and version
lineage to inputs, bridge, or formula when derived
```

This is a **conceptual sufficiency check**, not a proposal to impose a single giant mandatory JSON schema on every flake. Fields that are genuinely unavailable should be represented as unavailable rather than guessed.

Preserve distinctions between **missing and zero**, and between **UNKNOWN, false, not applicable, and undisclosed**. Preserve **reported, derived, and adjusted** as separate statuses. A reproducible calculation validates its lineage; it does not, by itself, validate the intended economic interpretation.

### 4.4. The database is not necessarily part of Tabularium

Tabularium's public Git repository can own the original and representation corpus, machine-consumable flake series, and minimal provenance/inventory infrastructure. A continuously maintained integrated relational or analytical database can live in a separate system, local environment, service, or another repository. It is not necessary to force a stateful or large database workload into Git.

This boundary permits multiple consumers and execution environments to reuse the same source-faithful corpus. A future database implementation is a downstream design decision, not a prerequisite for admitting a new flake series.

## 5. Views, marts, visualization, and analytical products

The expected route for **unified reporting and presentation** is:

```text
heterogeneous published series
  -> series-local machine artifacts (flakes)
  -> shared database ingestion and validated integration
  -> query/selection/explicit analytical operations
  -> view, mart, table, chart, API, report, or exported file
```

The downstream product can harmonize data **when a justified and documented mapping exists** and can calculate ratios, changes, indicators, rankings, and other derived outputs. These products are not edits to the underlying source publication, scroll, or flake. Their lineage should resolve back to inputs, including declared formulas and any assumptions.

This is a preferred architectural contract for reusable, cross-source analytical outputs: **build them from the integrated data contour**, not a growing network of bespoke direct-to-CSV scripts that each implement incompatible joins and mappings.

An ordinary source-local check or an operational notification need not wait for database ingestion; see Section 8.

## 6. Example paths and justified omissions

| Source scenario | Locally retained route | Why |
| --- | --- | --- |
| Complex Rosstat monthly XLSX, including future population/demographic series | `originals → flakes → database → outputs`; optionally `originals → scrolls → flakes` | Preserving source bytes matters; an AI-friendly full representation is optional if series extraction is more useful. |
| Rosstat PDF bulletin whose full text is useful to AI readers | `originals → scrolls → flakes → database` when PDF archival is justified; otherwise `scrolls → flakes` | Original retention and extraction are separable decisions. |
| Publisher HTML page containing text and data | `scrolls → flakes → database`, or only `scrolls` | A duplicate original HTML copy normally adds no useful representation. |
| Very large IFRS PDF publication | Source retrieved transiently → `scrolls`; optionally `flakes → database` | Local original-byte archival can be omitted because of its repository cost; the scroll remains a representation, not the original PDF. |
| Official statistical table loaded directly by a collector | External source → `flakes → database` | A stable programmatic capture may not warrant extra archived intermediate files; retain the necessary provenance. |
| Primary publication useful as narrative evidence but not yet extracted | `scrolls` only | No reason to create an empty flake or database row for a future possibility. |
| Native official series already suitable for algorithmic capture | Direct `flakes` when the series contract and source evidence justify it | Format compatibility can eliminate intermediate conversion without changing the artifact's meaning. |

All paths are **illustrative processing choices**, not instructions to migrate any existing publication automatically. One issue may have multiple representations where those representations provide distinct capabilities; it should not be physically duplicated under different names without a reason.

## 7. Fidelity, provenance, and version semantics across transitions

The conceptual evidence chain remains:

```text
source
  -> representation
  -> observation
  -> derivation / bridge
  -> analytical claim
```

It is **related to**, but not interchangeable with, the physical processing route. `originals/` generally houses source artifacts. `scrolls/` generally houses publication representations. `flakes/` houses repeatably addressable source-extracted data and assertions, which can include multiple observations per file. The integrated database can carry observations, identity mappings, source-faithful record copies, and *separate* derived layers. Views and products expose selected analytical results and claims.

One semantic operation can occur without adding a new physical folder, and one folder can hold more than one kind of file metadata. The important rule is to **make semantic changes explicit and traceable**.

### 7.1. Transition-specific verification

| Transition | Principal checks |
| --- | --- |
| Publisher → `originals/` | Exact bytes, release identity, retrieval evidence, integrity and corrected-version distinction |
| Publisher or `originals/` → `scrolls/` | Completeness and source fidelity of text, tables, notes, order, units, narrative and limitations |
| Publisher, `originals/`, or `scrolls/` → `flakes/` | Source-to-field traceability, series grain, values, statuses, labels, version-qualified schema, reproducible extraction |
| `flakes/` → database | Lossless source-meaning retention, stable ingestion identity, type handling, explicit mappings, no invented cross-series equivalence |
| Database → product | Reproducible formula and bridge chain, as-of/version consistency, output meaning, proper reporting of assumptions and uncertainty |

An extraction that faithfully copies a published number can still be analytically unsuitable for comparison with another published number. An integrated query is not evidence that a semantic bridge is valid.

### 7.2. Multiple dates and changing editions

Do not collapse source issue date, statistical reference period, data-collection date, revision vintage, and ingestion date into one date. A monthly publication can contain annual, quarterly, and monthly observations whose periods differ from the filename's month.

Do not replace a genuine historical change in field meaning, region perimeter, calculation base, or classification with a single smooth column unless a documented bridge supports that result. **Differences that cannot be bridged remain separate observations or series segments.**

## 8. Monitoring, updates, and useful analytics before database integration

The integrated database is the normal source for reusable cross-series marts, but it is **not the earliest stage where logic may run**.

### 8.1. Monitoring may occur at multiple boundaries

- **Acquisition/source-monitor level:** detect availability, changed URLs, content hash differences, release changes, extraction errors, and missing expected publications.
- **Scroll level:** detect changes to an AI-readable publication or the output of a faithful conversion.
- **Flake level:** compare current and prior series-compatible records; validate schema, values, unexpected shifts, omissions, outliers, or release coverage.
- **Database level:** run cross-series checks, integrated monitoring, richer calculations, and multi-source analytics.
- **Product level:** publish dashboards, reports, exports, and user-facing results.

These operations can coexist. The publication monitor should not be artificially delayed until the whole database pipeline finishes.

### 8.2. Flake-level analytical notifications are legitimate

A notification generated after updating a series-specific flake can include an important new reported value, a same-series difference, a change percentage, or an anomaly flag. This is particularly useful when the consumer needs to know about new data immediately.

**Keep the distinction between the stored evidence and the notification's derived text.** The new source value stays in the flake; the computation, comparison window, threshold rule, and alert interpretation belong to monitoring logic and its event/output record, not silently back into the source-faithful data file.

For example:

```text
official regional publication
  -> source-traceable per-release flake CSV
  -> compare with compatible prior edition
  -> send notification: "published total changed by ... compared with ..."
  -> later ingest both source observations into the integrated database
```

The alert should identify actual reference periods, capture versions, comparability caveats, and the formula if it displays a derived change. If source methodology or territorial coverage changed, the alert must not report an unqualified growth rate as if the observations were directly comparable.

This is an **intentional short path for operational insights**, not a replacement for the database-first architecture of general-purpose marts and visualizations.

## 9. Separation of ecosystem responsibilities

The conceptual sequence can govern multiple execution settings without prescribing one physical deployment:

| Responsibility | Natural owner or location |
| --- | --- |
| Source-preserving artifacts and AI-readable representations | Tabularium's `originals/` and `scrolls/`, as selectively admitted |
| Per-series algorithmic source-faithful artifacts | Tabularium's `flakes/`, when the series belongs in the public corpus |
| Reusable retrieval, extraction, novelty checks, and series-processing functions | Portable business-processing code, for example Stratbox |
| Scheduling, credentials, notifications, Git commits, storage destinations, and deployment-specific retries | Each executing environment or application |
| Unified data ingestion, storage, identity, temporal handling, and explicit mappings | Downstream integrated database service or application |
| Marts, charts, reports, APIs, and user interfaces | Downstream consumers using the integrated data environment |
| Early alerts from newly published source series | Monitoring/processing subsystem at the relevant source or flake boundary |

An integration architecture should allow the same extraction functions to be invoked from different environments without making GitHub Actions workflow definitions the universal business logic. Workflows are one execution adapter among others.

The corpus does not need a universal event bus, new mandatory registry, or database infrastructure to document this separation. Add such infrastructure only when observed series, reliability needs, or real consumers justify it.

## 10. Proposed repository evolution, explicitly not implemented here

### 10.1. Add `originals/` as a top-level source archive

The new name and conceptual responsibility are proposed for adoption. Its internal path logic should follow relevant `scrolls/` source routes, but directories should be created only for admitted source material. `originals/` is not a mandatory landing zone for every collector.

### 10.2. Clarify the contracts of existing roots

An eventual implementation should distinguish:

- `originals/`: optional untouched publisher bytes;
- `scrolls/`: AI-readable source-faithful publications/representations, some admitted directly;
- `flakes/`: series-level algorithm-readable source-faithful data and assertions, structured locally rather than universally harmonized;
- downstream database: integration not necessarily hosted in Tabularium;
- downstream output: projections and analytics from the unified data contour, except deliberately scoped operational alerts.

This proposed language would revise current rules that conflate native XLSX archival and AI-readable publications within the definition of `scrolls/`. Existing source-specific exceptions for direct flake captures must remain workable until any explicit contract update is reviewed.

### 10.3. Migrate cautiously, not wholesale

The native Rosstat XLSX series is a strong initial candidate for moving from `scrolls/` to `originals/`. Preserve each workbook's bytes and Git history, its source-oriented route, version distinctions, and the substantial series-specific extraction/reading instructions already associated with those workbooks. Update route documentation, referenced paths, and tests as needed.

Do not relocate existing Markdown bulletins into `originals/`; they are scroll representations. Do not backfill giant IFRS PDFs simply because a new root exists. Do not create empty mirrored routes or require a new manifest for every file. No bulk migration of flakes, database schema, or monitoring workflows follows automatically from this research.

### 10.4. Keep development decisions separate from corpus state

The present document is **development-layer research**. It does not amend repository README/AGENTS contracts, change admitted file formats, create storage directories, or trigger collectors. A later implementation should make each desired contract change explicit, verify the affected source series, and then test representative ingestion paths.

## 11. Design acceptance tests and unresolved implementation choices

An implementation consistent with this model should pass these tests:

1. A selected Rosstat XLSX is archived byte-for-byte in `originals/`, and scripts can extract repeatable series records without needing a fabricated Markdown conversion.
2. A readable HTML source is admitted to `scrolls/` directly without an automatic duplicate in `originals/`.
3. A large financial-reporting PDF can yield a faithful scroll without a local binary original; its external origin remains honestly identified.
4. Two different flake series can have incompatible schemas and still be valid flakes, while each remains programmatically usable under its own published contract.
5. A real methodological break within one series is not hidden by the promise of series-local alignment.
6. A downstream database can ingest both series and retain their distinct constructs, perimeters, dates, values, units, statuses, and provenance without claiming unwarranted equivalence.
7. A chart or unified report obtains its data through the integrated data contour and records any mappings/calculations it applies.
8. A flake-level update monitor can send a useful same-series alert before database ingestion, without storing the derived percentage as a publisher-reported value.
9. A publisher revision can be distinguished from an unchanged issue, and downstream outputs can identify the source version actually used.
10. The whole arrangement works if the integrated database and presentation systems run **outside** the Tabularium Git repository.

Remaining design choices should be decided only when implementing real source series: source-specific retention thresholds for heavy binaries; any use of Git LFS or external archive storage; whether particular statistical series require a full scroll as well as a flake; provenance detail appropriate for different extraction risks; and the physical database schema. None requires a new universal framework before `originals/` can be introduced.

## Final architectural judgment

**The five-stage route is a reusable processing model across the ecosystem, not a demand to house all five stages in Tabularium.** Its value comes from separating (a) untouched source preservation, (b) AI-reading suitability, (c) series-local algorithmic usability, (d) cross-series data integration, and (e) produced views and analytical outputs.

`originals/` fills a genuine preservation gap. `scrolls/` remains the AI-readable publication layer. `flakes/` becomes explicitly understood as a **machine-operable, source-faithful, potentially heterogeneous collection of series**, capable of driving scripts and early notifications before integration. A database provides the common contour, but conceptual comparability still requires evidence. Views and charts normally derive from that database, with explicit, limited short paths for operational alerts.

That separation is both flexible and strict: it allows a source to skip unnecessary conversions while preserving an exact boundary between what a publisher said, what a parser extracted, what a database integrated, and what an analyst or algorithm concluded.
