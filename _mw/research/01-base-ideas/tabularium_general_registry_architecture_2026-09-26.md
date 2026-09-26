# Tabularium: architecture of the general documentation registry and GitHub Pages interface

**Date:** 2026-09-26  
**Status:** architectural proposal / no implementation performed  
**Context:** Tabularium corpus registry, GitHub Pages, machine-readable inventory, human-readable coverage interface

---

## 1. Executive summary

The general registry should not be implemented as one enormous Markdown table.

The stronger architecture is:

```text
TABULARIUM SOURCE CORPUS
        ↓
FULL MACHINE INVENTORY
        ↓
PRESENTATION MODEL
        ↓
┌─────────────────────┬──────────────────────┐
│ compact Markdown    │ GitHub Pages         │
│ latest registry     │ interactive registry │
└─────────────────────┴──────────────────────┘
```

The core principle is:

> one semantic owner of the fact that an artifact exists, multiple derived views.

The authoritative source of existence remains the Git tree / source corpus.  
The registry is a deterministic projection of repository contents, not a manually maintained second database.

The recommended target state consists of:

1. one full machine-readable inventory;
2. the existing compact latest corporate-disclosures Markdown registry;
3. an interactive GitHub Pages interface;
4. data-quality reporting for unparsed or ambiguous artifacts.

The DOM.RF investor-relations presentation style is useful as a reference for the **entity/series view**, not for the global corpus matrix.

---

## 2. Current state of Tabularium

The current repository already contains several fundamentally different source families:

- corporate disclosures;
- IFRS;
- RAS;
- annual reports;
- issuer reports;
- Moscow Exchange recurring publications;
- SPB Exchange recurring publications;
- Bank of Russia forecasts;
- Rosstat recurring XLSX and Markdown publications;
- DOM.RF Analytics monthly series;
- remote Bank of Russia regulatory-reporting bridges.

These sources do not share one universal temporal model.

Examples:

```text
СБЕР_2026М6_МСФО.md
```

represents a reporting period.

```text
2026-07.md
```

in a monthly DOM.RF Analytics series represents a reference period.

```text
forecast_260724.md
```

represents a publication issue date.

Historical exchange HTML files may use source titles as filenames and derive year from their directory.

Therefore a universal matrix of:

```text
object × date × document
```

would eventually become semantically misleading unless temporal meaning is explicitly preserved.

The current:

```text
registry/corporate-disclosures.md
```

is already based on the correct conceptual model.

It is explicitly a:

> navigational projection of repository contents

and does not assert semantic equivalence between reports or reporting perimeters.

Its current limitation is intentional: it shows only the latest reporting period for each company/document-kind combination.

Therefore it should remain a **Latest view**, not become the canonical complete registry.

---

# 3. Recommended architecture

## 3.1. Source corpus remains authoritative

The source corpus remains the only authoritative physical layer:

```text
source artifact
→ repository path
→ Git blob / commit history
```

The registry must be fully rebuildable from it.

The registry must never become a manually curated second source of truth.

---

## 3.2. One full machine-readable inventory

Recommended canonical generated file:

```text
registry/
    corpus-inventory.jsonl
    corporate-disclosures.md
    README.md
```

`corpus-inventory.jsonl` should contain one record per:

- local publication artifact;
- explicitly documented remote bridge.

The grain is intentionally simple:

> one physical or logical corpus object = one inventory record.

Example for a corporate artifact:

```json
{
  "schema_version": "1",
  "object_type": "artifact",
  "availability": "local",
  "path": "russia/corporate-disclosures/financial-reporting/ifrs/2026/СБЕР_2026М6_МСФО.md",
  "git_blob_sha": "...",
  "size_bytes": 123456,
  "format": "md",
  "route": "corporate-disclosures/financial-reporting/ifrs",
  "entity_literal": "СБЕР",
  "period": {
    "literal": "2026М6",
    "kind": "reporting_period",
    "year": 2026,
    "month": 6
  },
  "document_kind_literal": "МСФО",
  "parser_id": "corporate-filename-v1",
  "parse_status": "PARSED"
}
```

Example for a recurring series:

```json
{
  "schema_version": "1",
  "object_type": "artifact",
  "availability": "local",
  "path": "russia/dom-rf-analytics/largest-mortgage-banks-results/2026/2026-07.md",
  "git_blob_sha": "...",
  "format": "md",
  "route": "dom-rf-analytics/largest-mortgage-banks-results",
  "series": "largest-mortgage-banks-results",
  "period": {
    "literal": "2026-07",
    "kind": "reference_period",
    "year": 2026,
    "month": 7
  },
  "parser_id": "monthly-reference-period-v1",
  "parse_status": "PARSED"
}
```

---

# 4. Inventory is not an Observation Layer

This distinction must remain explicit.

The inventory answers:

```text
what exists
where it exists
what structural attributes can be proven from route / filename / metadata
```

It does **not** contain:

- financial observations extracted from documents;
- canonical metrics;
- analytical conclusions;
- economic normalization;
- inferred semantic equivalence.

Therefore:

```text
source corpus
→ inventory
```

is a repository-navigation operation, not an analytical one.

This fits the existing Tabularium contract much better than introducing an observation or knowledge layer into the corpus prematurely.

---

# 5. Why JSONL

JSONL is preferable for the canonical inventory because it:

- scales cleanly;
- remains diff-friendly in Git;
- is easy for AI systems to consume;
- supports nested provenance fields;
- can be streamed;
- allows one record per artifact;
- avoids turning the entire registry into one giant JSON object.

CSV is weaker because nested provenance and period metadata become awkward.

Markdown is a view, not a machine contract.

A compact JSON object for GitHub Pages may be generated at build time, but it does not need to become a second canonical file.

---

# 6. Inventory semantics

## 6.1. Presence means presence only

A missing inventory record must mean only:

> the corresponding local artifact is not registered in the current corpus.

It must **not** mean:

- the publisher did not publish it;
- the disclosure does not exist;
- the value is zero;
- the value is not applicable;
- the information is unknown.

This distinction should be explicitly documented.

---

## 6.2. Remote bridges

Remote-source bridges should not be presented as if the dataset were locally stored.

Recommended distinction:

```text
● local artifact
◇ remote canonical bridge
empty = no local artifact registered
```

A bridge record may use:

```text
object_type = bridge
availability = remote
```

The UI should visually distinguish it from locally preserved source artifacts.

---

# 7. Scanner and parser architecture

The current corporate-disclosures generator combines several operations:

```text
discover file
→ parse filename
→ validate identity
→ select latest
→ render Markdown
```

That works well for the corporate route because the filename contract is intentionally strict.

The general registry should be decomposed.

Recommended pipeline:

```text
DISCOVERY
find all corpus artifacts
        ↓
INVENTORY
record every object without loss
        ↓
ROUTE-SPECIFIC PARSERS
attempt entity / series / period / kind parsing
        ↓
PARSE STATUS
PARSED / PARTIAL / UNPARSED
```

The key invariant:

> an unparsed artifact must never disappear from the inventory.

Instead it remains present with:

```text
parse_status = UNPARSED
```

and appears in the Data Quality view.

---

# 8. Route-specific parsers

Do not create a universal naming grammar for the entire corpus.

Start with explicit parsers for real source classes, for example:

```text
corporate_filename_v1
monthly_yyyy_mm_v1
cbr_forecast_issue_date_v1
rosstat_osn_v1
```

Historical exchange HTML may initially remain partially parsed.

This is preferable to premature creation of a large global `series-registry.yaml`.

A formal series registry should appear only when enough real source families require it.

---

# 9. GitHub Pages as the main human interface

The Pages site should not be one giant screen.

Recommended main views:

```text
Coverage
Companies & Institutions
Series
Inventory
```

Optionally:

```text
Data Quality
```

Each view is a projection of the same machine inventory.

---

# 10. View 1 — Coverage Matrix

This is the global dense matrix answering:

> what documentation is present across entities and periods?

Conceptually:

```text
                    2025                         2026
               M3   M6   M9   M12          M3   M6   M9   M12
────────────────────────────────────────────────────────────────
СБЕР            ●    ●    ●   ●●●           ●   ●●●
ВТБ             ●    ●    ●    ●            ●    ●
РСХБ            ●    ●    ●    ●            ●    ●
ГПБ                  ●         ●●                 ●●
ДОМ.РФ          ●●   ●●   ●●   ●●           ●●   ●●
```

Each dot represents a document kind.

Possible display vocabulary:

```text
● МСФО
● РСБУ
● презентация
● пресс-релиз
● годовой
● ESG
● отчет эмитента
```

However, the machine inventory must retain literal source-side naming.

Example:

```text
document_kind_literal = "МСФО_ПРЕЗ"
```

The visual style:

```text
blue dot
```

is a presentation mapping only.

If a new kind such as:

```text
МСФО_РЕЛИЗ
```

appears, the inventory must register it immediately even if the UI has no special color yet.

---

# 11. Year switching

The matrix should not grow horizontally forever.

Avoid:

```text
2023M3 | 2023M6 | ... | 2038M12
```

Use a year switcher:

```text
2026   2025   2024   2023   ALL
```

Within a selected year, show only relevant periods.

For ordinary corporate reporting:

```text
M3  M6  M9  M12
```

For monthly series:

```text
M1 M2 M3 ... M12
```

This preserves usability while still allowing full historical coverage.

---

# 12. DOM.RF-style entity view

The DOM.RF investor-relations presentation style is useful as a reference for **single-entity navigation**.

It should not replace the global matrix.

When a user opens an entity such as:

```text
ДОМ.РФ
```

the interface may show:

```text
ДОМ.РФ

[ 2026 ] [ 2025 ] [ 2024 ] [ ALL ]

2026
──────────────────────────────────────

6 месяцев
● МСФО
● Презентация
● Пресс-релиз
● Отчет эмитента

3 месяца
● МСФО
● Презентация

2 месяца
● Финансовые результаты

1 месяц
● Финансовые результаты
```

This model is especially strong for corporate issuers because users naturally think in:

```text
year
→ period
→ available documents
```

Large year sections and period cards can provide a cleaner, more investor-relations-like experience than a spreadsheet matrix.

---

# 13. Recurring-series view

Recurring publications should have a different projection.

For example, Moscow Exchange:

```text
МОСБИРЖА

2026

Trading results
Jan ●  Feb ●  Mar ●  Apr ● ... Dec ○

Retail investor activity
Jan ●  Feb ●  Mar ● ...

Index reviews
Mar ●  Jun ●  Sep ●  Dec ●

Trade volumes
Aug ●
```

This is more truthful than forcing Moscow Exchange into the same conceptual frame as quarterly IFRS reporters.

The same series-oriented model can be used for:

- Moscow Exchange;
- SPB Exchange;
- DOM.RF Analytics;
- Rosstat;
- Bank of Russia;
- other recurring institutional publications.

---

# 14. Quick filters as saved views

Special shortcuts such as:

```text
Мосбиржа
Сбер
ДОМ.РФ
Росстат
```

should not require hardcoded separate logic.

They should simply resolve to URL state.

Examples:

```text
?view=coverage&year=2026
```

```text
?view=entity&entity=СБЕР&year=2026
```

```text
?view=series&publisher=moex-exchange&year=2026
```

Advantages:

- bookmarkable;
- shareable;
- browser back/forward support;
- reproducible view state;
- easy linking from README or research documents.

Analytical filter state should live in the URL.

Presentation preferences may live in local browser storage.

---

# 15. Recommended filters

Avoid premature industry taxonomies such as:

```text
banks
developers
technology
```

unless they become a real repository requirement.

Start only with dimensions that are directly supported by corpus structure:

```text
Year
Country
Route
Entity / publisher
Publication series
Document kind literal
Format
Availability
Parse status
```

Plus free-text search.

This is enough for the first mature registry.

---

# 16. View 4 — Full Inventory

The full inventory should provide a technical corpus-browser view.

Possible columns:

```text
Path
Entity / Publisher
Series
Period
Kind
Format
Storage
Parse status
```

This view is useful for questions such as:

```text
did we actually upload this release?
```

```text
which HTML artifacts remain?
```

```text
which files could not be parsed?
```

```text
what is available for 2024?
```

The Pages interface therefore becomes not only a navigation surface but also a corpus QA tool.

---

# 17. Data Quality view

A lightweight Data Quality page would be highly valuable.

Example:

```text
Inventory build

436 local artifacts

Parsed
421

Partially parsed
10

Unparsed
5

Duplicate logical identities
0
```

Below that, show the unresolved artifacts.

This makes ambiguity visible rather than silently dropping it.

The correct Tabularium behavior is:

```text
UNKNOWN remains UNKNOWN
```

not:

```text
UNKNOWN disappears from the interface
```

---

# 18. Existing Markdown registry should remain

Do not replace:

```text
registry/corporate-disclosures.md
```

It answers a different question:

> what is the latest currently available reporting material for each entity and document type?

The new machine inventory answers:

> what exists in the corpus at all?

GitHub Pages answers:

> how can a human efficiently explore the corpus?

Therefore the three layers are complementary:

```text
latest Markdown projection
full machine inventory
interactive Pages interface
```

They should not be collapsed into one artifact.

---

# 19. Suggested technical implementation model

No heavy frontend framework is required initially.

Avoid introducing:

- React;
- Next.js;
- backend APIs;
- hosted databases;
- server-side runtime.

A simple architecture is sufficient:

```text
Git tree
   ↓
Python inventory builder
   ↓
registry/corpus-inventory.jsonl
   ↓
Python Pages model builder
   ↓
site-data/*.json
   ↓
HTML / CSS / JavaScript
   ↓
GitHub Pages
```

The generated Pages data does not necessarily need to be committed to `main`.

It can be created inside a temporary `_site/` directory during GitHub Actions and deployed as a Pages artifact.

This avoids polluting the repository with unnecessary build outputs.

---

# 20. Table library

Do not introduce a large table dependency immediately.

The Coverage Matrix is specialized enough that a small custom JavaScript renderer is likely simpler.

If the full Inventory eventually grows to many thousands of rows, a table library such as Tabulator may become useful for:

- header filters;
- sorting;
- grouping;
- frozen columns;
- virtualized rendering.

Possible future architecture:

```text
custom Coverage UI
custom Entity cards
custom Series calendar
Tabulator-powered Inventory
```

But the dependency should only be introduced when the corpus size makes it necessary.

---

# 21. GitHub Actions model

The user-facing operational model may remain very simple:

```text
Update corpus registry
```

One manually triggered workflow can perform:

```text
scan corpus
↓
validate inventory
↓
write corpus-inventory.jsonl
↓
update compact Markdown projection
↓
commit machine registry
↓
build Pages model
↓
deploy Pages
```

The key ordering rule is:

> evidence / inventory first, rendering second.

If the Pages renderer fails, the correctly generated machine registry should remain valid.

Pages deployment should therefore not be semantically upstream of the inventory.

---

# 22. Future directory migration

The design should not assume that:

```text
russia/
```

will always remain at repository root.

If Tabularium later moves toward something such as:

```text
corpus/
    russia/
    world/
```

or:

```text
database/
    russia/
    world/
```

the UI should remain unaffected.

Pages should consume inventory dimensions such as:

```text
country = russia
route = corporate-disclosures/...
```

The scanner owns physical path knowledge.

The frontend owns presentation.

This makes future corpus expansion much safer.

---

# 23. Recommended target state

```text
                          TABULARIUM SOURCE CORPUS
                                   │
                                   │ deterministic scan
                                   ▼
                      registry/corpus-inventory.jsonl
                       FULL, MACHINE-READABLE INDEX
                                   │
                 ┌─────────────────┼─────────────────┐
                 │                 │                 │
                 ▼                 ▼                 ▼
        current/latest MD     Pages data model     QA checks
            projection               │
                                     ▼
                              GitHub Pages UI
                                     │
              ┌──────────────────────┼──────────────────────┐
              ▼                      ▼                      ▼
        Coverage Matrix        Entity / Series         Full Inventory
                               DOM.RF-style
```

This produces a real **corpus catalog**, rather than merely a large documentation table.

A human gets an understandable view of coverage.

An AI gets one machine-readable inventory describing what is available.

The source corpus remains authoritative and source-faithful.

The registry remains a deterministic projection.

The Pages interface remains a replaceable presentation layer.

---

# 24. Recommended next design step

Before implementation, define the exact contract of:

```text
registry/corpus-inventory.jsonl
```

including at minimum:

```text
schema_version
object_type
availability
path
git_blob_sha
size_bytes
format
country
route
entity_literal
publisher_literal
series
document_kind_literal
period.literal
period.kind
period.year
period.month
parser_id
parse_status
```

Then design the exact UI contract for:

```text
Coverage
Entity / Institution
Series
Inventory
Data Quality
```

Only after the schema is stable should the implementation begin.

---

## Final principle

The system should preserve the Tabularium epistemic hierarchy:

```text
source
→ representation
→ inventory/navigation projection
→ observation
→ derivation/bridge
→ analytical claim
```

The general registry belongs between the physical source corpus and higher semantic layers.

It should answer:

> what exists, where is it, and how is it structurally classified?

It should not answer:

> what does it economically mean?

That boundary is what allows the registry to become large, durable, and machine-usable without undermining the source-faithful contract of Tabularium.
