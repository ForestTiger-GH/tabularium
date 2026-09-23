# Naming and semantic normalization of IFRS observations in Tabularium

**Status:** research / development-layer proposal\
**Scope:** IFRS financial statements and notes; naming, concept
identity, grouping, dimensions and aggregates\
**Repository:** `ForestTiger-GH/tabularium`\
**Date:** 2026-09-23

## Executive conclusion

The main conclusion is deliberately conservative: **Tabularium should
not try to "rename IFRS reports into one common vocabulary" inside the
source-faithful layer.** There is no single mandatory IFRS chart of
accounts or universal set of line-item names that every issuer must use.
IFRS defines recognition, measurement, presentation and disclosure
requirements; IFRS 18 additionally strengthens principles for
aggregation, disaggregation and faithful labels. But entities still
retain substantial judgement in presentation, grouping and wording.

The closest thing to an official common machine-readable vocabulary is
the **IFRS Accounting Taxonomy**. For 2026 reporting, the IFRS
Foundation states that the 2025 taxonomy remains current. It supplies
machine identifiers, standard human-readable labels, documentation
labels, data types, period properties, balance properties, references to
authoritative IFRS literature, presentation structures, calculations,
and---critically---dimensional modelling through line items, axes and
members.

Therefore the recommended Tabularium architecture is not:

`issuer label -> replace with Tabularium label`

but:

`source expression -> source observation -> semantic mapping -> canonical concept + dimensions -> optional bridge/derived concept`

The source wording must survive unchanged. Canonical terminology should
exist as a **parallel semantic registry**, not as a rewrite of the
source.

A robust observation should distinguish at least:

`concept × entity/perimeter × period × unit × dimensions × measurement/status × source/version`

This prevents the most dangerous failure mode: treating two values as
identical merely because their labels look similar.

------------------------------------------------------------------------

# 1. The actual problem

When many IFRS reports are collected, apparent synonymy appears
everywhere:

-   `Loans to customers`
-   `Loans and advances to customers`
-   `Loans and advances to customers, net`
-   `Customer loans`
-   `Loans to legal entities`
-   `Corporate loans`
-   `Loans at amortised cost`
-   `Loans and advances to customers at amortised cost`
-   `Net loans and advances to customers`
-   `Gross carrying amount of loans`
-   `Loans before allowance for expected credit losses`

These are not merely alternative spellings of one metric.

They can differ by:

-   gross versus net carrying amount;
-   expected-credit-loss allowance treatment;
-   measurement category;
-   counterparty definition;
-   legal versus economic sector;
-   consolidation perimeter;
-   inclusion of banks or financial institutions;
-   product composition;
-   accrued interest;
-   fair-value adjustments;
-   repos or reverse repos;
-   assets held for sale;
-   currency;
-   geography;
-   stage or credit quality;
-   maturity;
-   reporting date;
-   accounting-policy version.

A single string field called `metric_name` cannot safely represent this.

The naming problem is therefore actually **three separate problems**:

1.  **Lexical normalization** --- different words for the same
    accounting concept.
2.  **Semantic identification** --- determining whether the accounting
    meaning is actually the same.
3.  **Dimensional decomposition** --- separating the base concept from
    the characteristics by which it is broken down.

Only the first problem is fundamentally about naming. The second and
third are data modelling problems.

------------------------------------------------------------------------

# 2. What IFRS itself standardises---and what it does not

## 2.1 IFRS is not a universal chart of accounts

IFRS Accounting Standards do not prescribe a universal bank chart of
accounts with one immutable label for every possible reported number.
Financial statements are principles-based and contain both required
presentation/disclosure concepts and entity-specific disclosures.

This matters because "canonical IFRS terminology" cannot simply be
created by choosing the most common wording from Russian bank reports.

The common semantic reference should instead be built from:

1.  IFRS Accounting Standards;
2.  IFRS Accounting Taxonomy;
3.  common-practice taxonomy elements;
4.  issuer-specific concepts when the first three are insufficient;
5.  explicit Tabularium bridges where equivalence or transformation is
    justified.

## 2.2 IFRS 18 changes the importance of labels

IFRS 18, effective for annual periods beginning on or after 1 January
2027 with earlier application permitted, is especially relevant to this
architecture.

Its aggregation/disaggregation logic is conceptually useful for
Tabularium:

-   items are aggregated based on **shared characteristics**;
-   items are disaggregated based on **dissimilar characteristics**;
-   characteristics can include nature, function, measurement basis and
    other characteristics;
-   labels and descriptions must faithfully represent the
    characteristics of the item;
-   a generic label such as `other` is not supposed to become a semantic
    dumping ground when a more informative description is possible.

This is very close to the principle Tabularium needs: **a label is a
representation of characteristics, not the identity of the observation
itself.**

## 2.3 IFRS permits entity-specific concepts

Digital IFRS guidance explicitly anticipates entity-specific extensions.
The IFRS Foundation recommends not creating an extension merely because
the issuer uses different wording if an existing taxonomy concept has
the same accounting meaning. But when no taxonomy element represents the
disclosure, an entity-specific extension is legitimate.

That gives Tabularium an important rule:

> **Different wording does not require a different canonical concept;
> different meaning does.**

And the reverse:

> **Similar wording does not prove identical meaning.**

------------------------------------------------------------------------

# 3. The IFRS Accounting Taxonomy as the primary naming backbone

For the purpose of canonical terminology, the IFRS Accounting Taxonomy
is much more useful than a hand-made glossary.

The taxonomy distinguishes several kinds of semantic objects.

## 3.1 Line item

A **line item** represents a reportable accounting concept. It may be
numeric or narrative.

Examples in principle:

-   assets;
-   cash and cash equivalents;
-   profit or loss;
-   interest revenue;
-   property, plant and equipment;
-   description of an accounting policy.

For Tabularium this maps naturally to a **base concept**.

## 3.2 Axis

An **axis** represents a characteristic by which one or more line items
can be broken down.

Examples of the type of distinction:

-   class of financial instrument;
-   component of equity;
-   geographical area;
-   operating segment;
-   maturity;
-   credit-risk stage.

For Tabularium an axis should normally become a **dimension type**, not
part of the metric name.

## 3.3 Member

A **member** is a value/category on an axis.

Conceptually:

`Loans and advances`\
+ `Credit risk stage axis = Stage 2 member`

is preferable to inventing a new atomic concept:

`Stage 2 loans and advances`.

The latter causes concept explosion.

## 3.4 Table

A taxonomy table connects line items and axes into a valid disclosure
structure. It expresses which dimensions logically apply to which
concepts.

For Tabularium this is useful as a model for **observation families** or
disclosure schemas. It should not be confused with the visual Markdown
table in the source transcription.

## 3.5 Labels

The IFRS Taxonomy separates machine identity from human wording.

Important label roles include:

-   **standard label** --- concise human-readable description of
    accounting meaning;
-   **documentation label** --- fuller textual explanation of accounting
    meaning;
-   presentation-specific labels;
-   negated labels;
-   total/net/terse variants where relevant.

This is a decisive architectural clue: **the identifier and the
displayed label are different things**.

Tabularium should copy this principle.

------------------------------------------------------------------------

# 4. Recommended naming model for Tabularium

A canonical object should not be identified by its English label. It
needs a stable ID.

Recommended minimum:

``` yaml
concept_id: ifrs:LoansAndAdvancesToCustomers
canonical_label: Loans and advances to customers
source_label: Кредиты и авансы клиентам
mapping_status: mapped_exact
```

But in real banking data that is not enough. The observation should be
compositional:

``` yaml
observation:
  concept_id: ...
  source_label: ...
  entity_id: ...
  reporting_perimeter: ...
  period: ...
  unit: ...
  dimensions:
    measurement_basis: ...
    gross_net_basis: ...
    counterparty_class: ...
    product_class: ...
    credit_risk_stage: ...
    geography: ...
  reported_status: reported
  source_locator: ...
  mapping:
    status: ...
    basis: ...
```

The exact storage syntax can be decided later. The semantic separation
is the important part.

------------------------------------------------------------------------

# 5. Four names that should coexist

For each mapped concept, Tabularium should ideally preserve four
distinct naming fields.

## 5.1 `source_label`

Literal wording from the publication.

Examples:

``` text
Loans and advances to customers
Loans to customers
Кредиты и авансы клиентам
Средства клиентов
```

Never silently modify this field.

## 5.2 `canonical_label`

Stable, human-readable Tabularium label.

Its purpose is navigation and comparison, not source transcription.

Example:

``` text
Loans and advances to customers
```

## 5.3 `concept_id`

Stable machine identifier independent of wording.

Example style:

``` text
ifrs:LoansAndAdvancesToCustomers
```

If an official IFRS taxonomy element is used, preserve its official
taxonomy identity/version rather than inventing a competing ID.

For Tabularium-specific concepts:

``` text
tab:CustomerLoansGross
```

or another stable namespace.

## 5.4 `display_label`

Optional context-sensitive rendering.

For example, a user-facing table may display:

``` text
Corporate loans — gross, Stage 3
```

even though the stored semantics are:

``` text
concept = loans
counterparty = corporate
basis = gross
stage = 3
```

`display_label` is presentation. It must never become semantic identity.

------------------------------------------------------------------------

# 6. Canonical terminology should be compositional

The most important design decision is to avoid an enormous flat
dictionary such as:

``` text
LoansCorporateGrossStage1RUBRussia
LoansCorporateGrossStage2RUBRussia
LoansCorporateGrossStage3RUBRussia
LoansRetailGrossStage1RUBRussia
...
```

That architecture eventually becomes unmaintainable.

Instead:

``` text
base concept
+ dimensions
+ members
+ period
+ unit
+ perimeter
+ accounting basis
```

## 6.1 Example: loan portfolio

A value may be represented conceptually as:

``` yaml
concept: LoansAndAdvances
dimensions:
  counterparty: CorporateCustomers
  carrying_basis: Gross
  credit_risk_stage: Stage3
  measurement_category: AmortisedCost
```

Another observation:

``` yaml
concept: LoansAndAdvances
dimensions:
  counterparty: RetailCustomers
  carrying_basis: Net
  product: Mortgage
```

The dimensions---not the spelling of the metric---carry the
distinctions.

## 6.2 Example: customer funding

Instead of separate unrelated names:

-   retail deposits;
-   individual customer deposits;
-   household term deposits;
-   corporate current accounts;
-   legal-entity current accounts;

use a common base family plus dimensions when source meaning supports
it:

``` yaml
concept: CustomerFunds
dimensions:
  customer_class: Individuals
  instrument: TermDeposit
```

or:

``` yaml
concept: CustomerFunds
dimensions:
  customer_class: Corporate
  instrument: CurrentAccount
```

However, this decomposition is allowed only when the source disclosure
genuinely supports it. A source line `Customer accounts` cannot
automatically be decomposed into current accounts and deposits.

------------------------------------------------------------------------

# 7. The canonical dimensions Tabularium is likely to need for IFRS banks

This should begin as a **small governed set**, not a universal ontology.

## 7.1 Entity and reporting perimeter

This is not merely metadata.

Possible distinctions:

-   consolidated group;
-   parent bank;
-   subgroup;
-   continuing operations;
-   discontinued operation;
-   banking group versus broader ecosystem group.

`Sberbank PJSC` and `Sber Group` are not interchangeable observations.

Recommended fields:

``` text
reporting_entity
reporting_perimeter
consolidation_basis
```

## 7.2 Time

Separate:

-   instant;
-   duration;
-   beginning of period;
-   end of period;
-   comparative period;
-   year-to-date;
-   quarter-only where actually reported;
-   restated comparative.

Never infer a quarterly flow by subtracting six-month and three-month
figures inside the reported observation layer. That is a derivation.

## 7.3 Unit and currency

Separate:

-   currency;
-   scale;
-   unit type.

Examples:

``` yaml
currency: RUB
scale: million
unit_type: monetary
```

versus:

``` yaml
unit_type: percent
```

or:

``` yaml
unit_type: shares
```

The literal source unit must remain recoverable.

## 7.4 Gross/net and allowance basis

This dimension is indispensable for banking statements.

Possible members:

-   gross carrying amount;
-   loss allowance;
-   net carrying amount;
-   carrying amount where gross/net semantics are not separately
    established;
-   UNKNOWN.

Never infer `net` merely because the statement is a balance sheet unless
the accounting presentation and note linkage support it.

## 7.5 Measurement basis/category

Examples:

-   amortised cost;
-   fair value through profit or loss;
-   fair value through other comprehensive income;
-   historical cost where applicable;
-   other/source-specific;
-   UNKNOWN.

A security at amortised cost and a security at FVOCI are not the same
observation even if both are called `Debt securities`.

## 7.6 Counterparty

Examples:

-   central banks;
-   credit institutions;
-   corporate customers;
-   individuals;
-   government;
-   related parties;
-   other.

Do not force issuer categories into a global hierarchy until equivalence
is demonstrated.

## 7.7 Product/instrument

Examples:

-   mortgage;
-   consumer;
-   credit card;
-   auto;
-   SME;
-   corporate;
-   interbank;
-   bonds;
-   deposits;
-   current accounts.

A product dimension and a counterparty dimension should remain separate
even when an issuer mixes them in one disclosure hierarchy.

## 7.8 Credit quality / IFRS 9 impairment

Potential axes:

-   Stage 1;
-   Stage 2;
-   Stage 3;
-   purchased or originated credit-impaired;
-   not subject to ECL;
-   credit-impaired/non-credit-impaired where separately disclosed.

Do not assume every issuer's internal quality buckets map one-to-one to
IFRS 9 stages.

## 7.9 Geography

Keep source geography as reported. Do not silently map:

`Russia / CIS / Other`

to another issuer's:

`Russia / Europe / Asia / Other`.

A bridge can later establish a coarser common geography.

## 7.10 Segment

Operating segments are issuer-defined under IFRS 8. `Retail Banking` at
Bank A is not automatically the same construct as `Retail Business` at
Bank B.

Segments therefore require issuer-specific members by default, with
optional analytical bridges.

## 7.11 Maturity

Keep source buckets literally:

-   on demand;
-   less than 1 month;
-   1--3 months;
-   3--12 months;
-   1--5 years;
-   more than 5 years.

Do not normalize bucket boundaries by rewriting source observations. A
harmonized maturity grid is a derivation/bridge.

------------------------------------------------------------------------

# 8. Aggregates require explicit semantic treatment

An aggregate is not just another label.

Consider:

``` text
Customer funds = current accounts + term deposits
```

This relationship may be true for one issuer and not explicitly
established for another. Even when arithmetic reproduces the total, the
economic perimeter may differ.

Recommended aggregate metadata:

``` yaml
aggregate_status: reported
components:
  - ...
calculation_relationship:
  source_supported: true
```

Versus a Tabularium-created total:

``` yaml
aggregate_status: derived
formula: ...
inputs: [...]
```

The two must never share an undifferentiated status.

## 8.1 Recommended statuses

At minimum:

``` text
reported
derived
adjusted
```

and separately:

``` text
present
missing
unknown
not_applicable
undisclosed
```

A zero is a reported numeric value. It is not `missing`.

------------------------------------------------------------------------

# 9. Mapping statuses: do not force certainty

A canonical terminology system needs uncertainty as a first-class
object.

Recommended mapping states:

``` text
EXACT
BROADER
NARROWER
RELATED
COMPOSITE
SOURCE_SPECIFIC
AMBIGUOUS
UNMAPPED
```

Possible meaning:

### EXACT

Source concept and canonical concept have the same accounting meaning
for the relevant context.

### BROADER

Source concept includes the canonical concept plus additional material.

### NARROWER

Source concept is a subset of the canonical concept.

### RELATED

Semantically related, but neither equivalent nor a clean subset.

### COMPOSITE

The source line combines multiple canonical concepts.

### SOURCE_SPECIFIC

Valid issuer-specific construct with no suitable canonical equivalent.

### AMBIGUOUS

Available evidence does not support a unique mapping.

### UNMAPPED

Mapping has not yet been performed.

This is much safer than a boolean `mapped = true/false`.

------------------------------------------------------------------------

# 10. Official IFRS taxonomy element versus Tabularium concept

Not every useful Tabularium concept should pretend to be an IFRS
taxonomy concept.

Recommended namespaces:

``` text
ifrs:...
tab:...
issuer:...
```

## `ifrs:`

Use when the accounting meaning corresponds to an official IFRS
Accounting Taxonomy element.

Store:

``` yaml
taxonomy: IFRS Accounting Taxonomy
taxonomy_version: 2025
element_name: ...
standard_label: ...
documentation_label: ...
references: ...
```

## `tab:`

Use only when Tabularium needs a stable cross-source concept not
represented adequately by one official taxonomy element.

Such a concept needs:

-   definition;
-   inclusion rules;
-   exclusion rules;
-   dimensional applicability;
-   provenance;
-   relationship to IFRS elements;
-   version;
-   examples;
-   counterexamples.

## `issuer:`

Use for genuinely entity-specific concepts.

An issuer-specific concept is not a failure. It is often the correct
source-faithful representation.

------------------------------------------------------------------------

# 11. Naming convention for canonical labels

The human-readable label should be boring, stable and precise.

Recommended rules:

1.  Use English, matching the repository's control-language convention.
2.  Prefer IFRS Taxonomy standard labels where an exact official concept
    exists.
3.  Do not encode dimensions in the base label when they can be
    represented structurally.
4.  Do not include the issuer name in a canonical concept.
5.  Do not include period or currency in the concept name.
6.  Do not include units such as `RUB million` in the concept name.
7.  Avoid abbreviations in canonical labels unless they are stable
    IFRS/industry terms.
8.  Preserve abbreviations and wording in `source_label`.
9.  Use singular/plural according to the official taxonomy concept where
    applicable rather than inventing a house style.
10. Treat `net`, `gross`, `before allowance`, `after allowance`,
    `at amortised cost`, etc. as semantic qualifiers, never cosmetic
    words.
11. Use `other` only when it is genuinely the source/canonical residual
    category and preserve its parent context.
12. Never collapse `profit`, `profit attributable to owners`,
    `profit from continuing operations`, and `comprehensive income` into
    one family merely because all are "earnings".

------------------------------------------------------------------------

# 12. Machine identifier convention

Human labels change. IDs should not.

If Tabularium creates its own IDs, recommended properties are:

-   ASCII;
-   stable;
-   language-neutral in practice;
-   no period;
-   no currency;
-   no entity name unless issuer-specific;
-   no unit;
-   no display punctuation;
-   versioned definition, not versioned ID, unless the meaning itself
    changes incompatibly.

Example:

``` text
tab:CustomerFunds
tab:GrossCarryingAmount
tab:LossAllowance
tab:NetCarryingAmount
```

Avoid IDs such as:

``` text
tab:SberLoans2026RUBmn
```

because they mix concept, entity, time and unit.

------------------------------------------------------------------------

# 13. Why labels must not carry sign semantics

Financial statements often display expenses, allowances or outflows in
parentheses while the underlying machine value may follow another sign
convention.

The IFRS Taxonomy itself supports special label roles such as negated
labels. This is a warning that:

**display sign ≠ economic meaning ≠ stored numeric sign**

Tabularium should therefore preserve:

``` text
source_lexeme
parsed_numeric_value
display_sign
semantic_balance/sign convention
```

as distinct concepts where structured extraction is performed.

For the raw Markdown transcription, of course, the literal source sign
remains untouched.

------------------------------------------------------------------------

# 14. A practical hierarchy for banking IFRS terminology

The following is a useful *semantic registry structure*, not a proposed
physical repository directory tree.

``` text
Financial position
├── Assets
│   ├── Cash and cash equivalents
│   ├── Due from / placements with financial institutions
│   ├── Loans and advances
│   ├── Securities / financial assets
│   ├── Derivative financial assets
│   ├── Property and equipment
│   ├── Intangible assets
│   ├── Deferred tax assets
│   └── Other assets
├── Liabilities
│   ├── Due to financial institutions
│   ├── Customer funds/accounts
│   ├── Debt securities issued
│   ├── Subordinated debt
│   ├── Derivative financial liabilities
│   ├── Tax liabilities
│   └── Other liabilities
└── Equity
    ├── Share capital
    ├── Share premium
    ├── Treasury shares
    ├── Reserves
    ├── Retained earnings
    └── Non-controlling interests

Financial performance
├── Interest income / interest revenue
├── Interest expense
├── Net interest income
├── Fee and commission income
├── Fee and commission expense
├── Net fee and commission income
├── Trading / fair-value results
├── Foreign-exchange results
├── Credit-loss / impairment expense
├── Operating expenses
├── Profit before tax
├── Income tax
├── Profit
├── Attribution of profit
└── Other comprehensive income

Cash flows
├── Operating activities
├── Investing activities
└── Financing activities

Financial instruments and risk
├── Measurement categories
├── ECL
├── Credit quality
├── Collateral
├── Concentration
├── Maturity
├── Liquidity
├── Market risk
└── Fair value

Capital and regulatory disclosures
...
```

But this tree should be treated as a **navigation view over concepts**,
not proof that every issuer's disclosures are equivalent.

------------------------------------------------------------------------

# 15. Example: how one reported loan number should be represented

Suppose a bank reports:

> Loans and advances to customers at amortised cost, net --- 4,850,000
> RUB million

The wrong model is:

``` yaml
metric: loans
value: 4850000
```

A better model:

``` yaml
source_observation:
  source_label: "Loans and advances to customers at amortised cost, net"
  source_value: "4,850,000"
  source_unit: "RUB million"
  source_locator:
    statement_or_note: "..."
    page: ...
    table: ...
    row: ...
    column: ...

semantic_mapping:
  concept_id: ...
  mapping_status: EXACT
  dimensions:
    measurement_category: amortised_cost
    carrying_basis: net
    counterparty: customers

observation_context:
  reporting_entity: ...
  reporting_perimeter: consolidated_group
  period_type: instant
  period_end: 2026-06-30
  currency: RUB
  scale: 1000000

status:
  provenance: reported
```

If `net` is only inferred from accounting practice and not supported by
the source context, the system must not quietly add it.

------------------------------------------------------------------------

# 16. Example: when two identical labels are different constructs

Issuer A:

``` text
Customer accounts
```

includes retail and corporate current accounts and deposits.

Issuer B:

``` text
Customer accounts
```

excludes certain financial institutions classified separately.

The lexical label is identical.

Canonical mapping must therefore consider:

``` text
definition
scope
counterparty population
instrument population
measurement
source note
accounting policy
```

Result may be:

``` text
A -> canonical concept X: EXACT
B -> canonical concept X: NARROWER
```

or two separate issuer-specific concepts.

This is precisely why `construct ≠ observation`.

------------------------------------------------------------------------

# 17. Example: when different labels may map to the same concept

Issuer A:

``` text
Cash and cash equivalents
```

Issuer B:

``` text
Cash and cash equivalents at the end of the reporting period
```

If the accounting meaning, perimeter, period and definition match the
same IFRS taxonomy concept, both can map to the same canonical concept
while retaining their literal labels.

No source text is lost.

------------------------------------------------------------------------

# 18. Example: notes with multidimensional tables

Consider an ECL table:

                      Stage 1   Stage 2   Stage 3   Total
  ----------------- --------- --------- --------- -------
  Corporate loans         ...       ...       ...     ...
  Mortgage loans          ...       ...       ...     ...

Do **not** create eight or twelve unrelated metric names.

Represent:

``` text
concept = GrossCarryingAmount / LossAllowance / LoansAndAdvances
product_or_counterparty = Corporate / Mortgage
credit_risk_stage = Stage1 / Stage2 / Stage3 / Total
```

subject to the actual meaning of the source table.

The column `Total` is also semantically important: it can be a reported
aggregate and should not automatically be replaced by the sum of stages
even if arithmetic matches.

------------------------------------------------------------------------

# 19. A canonical registry should contain definitions, not just synonyms

A synonym dictionary is insufficient.

Bad:

``` yaml
loans:
  synonyms:
    - loans
    - loans and advances
    - customer loans
```

Better:

``` yaml
concept:
  id: ...
  label: ...
  definition: ...
  concept_class: monetary_line_item
  period_type: instant
  expected_dimensions:
    - measurement_category
    - carrying_basis
    - counterparty
  source_basis:
    - IFRS taxonomy element ...
  inclusion_rules: ...
  exclusion_rules: ...
  related_concepts: ...
  broader_concepts: ...
  narrower_concepts: ...
  deprecated_aliases: ...
  version: ...
```

Aliases help discovery. They do not determine mapping.

------------------------------------------------------------------------

# 20. Mapping must be evidence-based

Recommended mapping evidence hierarchy:

### Level A --- explicit digital taxonomy identity

The issuer's official digital filing tags the fact with an IFRS taxonomy
element.

Strong evidence, but still preserve filing context and dimensions.

### Level B --- explicit accounting definition

The note or accounting policy defines the line sufficiently to establish
identity.

### Level C --- statement-note reconciliation

The statement line is explicitly linked to a note whose composition
establishes meaning.

### Level D --- source structure and wording

The table heading, row/column hierarchy and surrounding text support the
mapping.

### Level E --- lexical similarity only

Weak evidence. Should not normally produce `EXACT` by itself.

A mapping record should retain the evidence used.

------------------------------------------------------------------------

# 21. Digital filings are especially valuable

Where an issuer publishes XHTML/iXBRL/XBRL, Tabularium should treat the
digital tags as a first-class source representation.

They can expose:

-   official taxonomy element;
-   issuer extension element;
-   dimensions;
-   context;
-   period;
-   unit;
-   scale/decimals;
-   calculation/presentation relationships.

This can dramatically reduce manual terminology mapping.

But digital tagging is not infallible. A filed tag is evidence of how
the issuer represented the disclosure digitally; it should not be
silently treated as an unquestionable economic reinterpretation.

------------------------------------------------------------------------

# 22. Versioning is mandatory

Canonical semantics will evolve.

The registry should therefore distinguish:

``` text
registry_version
IFRS_taxonomy_version
concept_definition_version
mapping_version
source_version
```

For 2026, the IFRS Foundation states that the IFRS Accounting Taxonomy
2025 remains the current taxonomy for 2026 reporting periods.

When a future taxonomy deprecates or replaces elements, Tabularium
should not rewrite historical source mappings silently.

Recommended approach:

``` yaml
mapping:
  taxonomy: IFRS Accounting Taxonomy
  taxonomy_version: 2025
  element: ...
```

and a separate cross-version equivalence table.

------------------------------------------------------------------------

# 23. IFRS 18 transition must be explicit

The corpus will contain reports prepared:

-   under IAS 1 presentation;
-   under IFRS 18 after adoption;
-   possibly under IFRS 18 through early application.

Do not assume a line item with the same label before and after
transition has identical presentation semantics.

Especially relevant:

-   operating category;
-   investing category;
-   financing category;
-   required subtotals;
-   management-defined performance measures;
-   expense presentation;
-   aggregation/disaggregation.

Store the applicable presentation regime as part of report metadata or
mapping context.

------------------------------------------------------------------------

# 24. Management-defined performance measures must remain distinct

IFRS 18 formalises management-defined performance measures (MPMs) for
qualifying subtotals used in public communications.

For Tabularium this supports a broader principle:

``` text
IFRS-defined / required subtotal
≠
management-defined performance measure
≠
Tabularium-derived analytical metric
```

Even when all three are called something like
`adjusted operating profit`.

Recommended provenance class:

``` text
reported_ifrs
reported_management_defined
derived_tabularium
```

with the original disclosure retained.

------------------------------------------------------------------------

# 25. Do not normalize accounting policy differences away

Two banks may both report `Interest income`, but the underlying
classification can change due to:

-   accounting policy;
-   financial instrument category;
-   effective-interest-method treatment;
-   presentation choices;
-   IFRS 18 adoption;
-   reclassification/restatement.

Canonical naming should facilitate comparison, not certify
comparability.

Therefore each mapping can have a separate comparability assessment:

``` text
semantic_identity
presentation_comparability
measurement_comparability
period_comparability
perimeter_comparability
```

This belongs in the bridge/development layer, not in raw source
artifacts.

------------------------------------------------------------------------

# 26. Proposed semantic layers for Tabularium

A clean architecture can be expressed as five layers.

## L0 --- Source

Original publication:

``` text
PDF / XHTML / XLSX / HTML / XBRL / ...
```

Immutable evidence.

## L1 --- Representation

Source-faithful Markdown or native machine-readable source.

No canonical renaming.

## L2 --- Observation

Atomic source facts with literal source semantics and provenance.

Example:

``` text
row = "Loans and advances to customers"
column = "30 June 2026"
value = ...
```

## L3 --- Semantic mapping / bridge

Maps source observations to canonical concepts and dimensions.

This is where terminology unification belongs.

## L4 --- Derivation / analytical claim

Ratios, harmonized aggregates, peer comparisons, analytical
classifications.

Not source evidence.

This is exactly compatible with:

`source → representation → observation → derivation/bridge → analytical claim`

The terminology registry should primarily serve the transition from
observation to bridge---not mutate L0/L1.

------------------------------------------------------------------------

# 27. Physical repository implications

Current Tabularium rules say:

-   source-faithful primary artifacts only;
-   no analysis or normalization in source artifacts;
-   native machine-readable formats stay native;
-   PDFs become complete source-faithful Markdown;
-   financial reporting is routed under the established IFRS family;
-   reporting perimeter is part of source identity.

Therefore a terminology system should **not require reorganizing
existing IFRS source directories**.

The safest initial implementation is a development-layer registry
separate from the report artifacts.

For example, conceptually:

``` text
development/
  ifrs-semantic-registry/
    README.md
    concepts/
    dimensions/
    mappings/
    validation/
```

But the actual path should be introduced only if the repository contract
is intentionally expanded to permit this development layer. Under the
current `AGENTS.md`, analytical/research methodology is out of scope for
the corpus itself. So the first implementation may be better kept in a
separate development branch/repository or formal proposal until the
contract is amended.

**Do not create empty architecture before there is a real mapping
workload.**

------------------------------------------------------------------------

# 28. Minimal viable registry

The first production iteration does not need thousands of concepts.

Start with the concepts actually observed in the collected bank reports.

Recommended fields:

``` yaml
id:
label:
object_type: line_item | axis | member | narrative | subtotal
namespace: ifrs | tab | issuer
definition:
ifrs_taxonomy:
  version:
  element:
  standard_label:
  documentation_label:
period_type:
data_type:
balance_type:
broader:
narrower:
related:
allowed_dimensions:
status:
version:
```

Dimension definition:

``` yaml
id:
label:
definition:
members:
source_basis:
version:
```

Mapping:

``` yaml
source_id:
source_locator:
source_label:
source_context:
target_concept:
dimensions:
mapping_status:
mapping_evidence:
mapping_notes:
mapping_version:
```

------------------------------------------------------------------------

# 29. Recommended first controlled dimensions

Do not begin with fifty dimensions.

For Russian banking IFRS, the first set could be:

``` text
reporting_perimeter
period
currency
scale
measurement_category
gross_net_basis
counterparty_class
product_class
credit_risk_stage
instrument_class
maturity_bucket
geography
segment
```

Then add a dimension only when a real source disclosure requires it.

This follows Tabularium's general rule: architecture should emerge from
sources, not from speculative universality.

------------------------------------------------------------------------

# 30. Canonicalisation workflow

## Step 1 --- inventory literal labels

Extract unique labels and their locations from existing IFRS reports.

Do not normalize yet.

Output conceptually:

``` text
issuer
report
statement/note
table
row/column
literal label
period type
unit
```

## Step 2 --- cluster candidates

Group lexically and structurally similar labels for human review.

This is candidate generation, not mapping.

## Step 3 --- query IFRS Accounting Taxonomy

For each candidate, search:

-   standard labels;
-   documentation labels;
-   common-practice elements;
-   presentation groups;
-   dimensions/members;
-   references.

## Step 4 --- inspect source definition

Read the accounting policy, note and reconciliation.

## Step 5 --- assign mapping status

`EXACT`, `BROADER`, `NARROWER`, etc.

## Step 6 --- separate dimensions

Move true characteristics out of the base concept where justified.

## Step 7 --- validate arithmetic relationships

Use reported totals and components as consistency checks.

Arithmetic consistency is evidence of structure, not proof of economic
equivalence.

## Step 8 --- peer validation

Compare the proposed mapping across multiple banks.

A mapping that works for one issuer may fail on another.

## Step 9 --- version and freeze

Once reviewed, release a registry version.

## Step 10 --- never rewrite the raw source

Mappings can improve over time without changing the evidence layer.

------------------------------------------------------------------------

# 31. Automated mapping: what AI can and cannot safely do

AI is useful for:

-   extracting candidate labels;
-   finding similar IFRS taxonomy labels;
-   identifying likely dimensions;
-   finding note definitions;
-   proposing candidate mappings;
-   detecting inconsistent mappings;
-   generating review queues.

AI should not silently decide:

-   that two constructs are economically equivalent;
-   that a gross/net distinction is immaterial;
-   that missing means zero;
-   that issuer segment definitions are comparable;
-   that two maturity grids can be merged;
-   that an aggregate can be reconstructed from components;
-   that a source-specific extension is unnecessary.

Recommended automation output:

``` yaml
candidate_target: ...
confidence: ...
evidence:
  - ...
conflicts:
  - ...
requires_review: true
```

Confidence is workflow metadata, not semantic truth.

------------------------------------------------------------------------

# 32. Validation rules

A useful registry should be machine-testable.

Examples:

### Identity validation

Every concept ID is unique.

### Label validation

Every concept has one canonical English label.

### Source preservation

Every mapping retains the exact source label and source locator.

### Dimensional validity

Only permitted dimensions can be attached to a concept.

### Member validity

A dimension member belongs to the correct axis.

### Period validity

An instant concept cannot silently receive a duration context without an
explicit exception.

### Unit validity

A monetary concept cannot silently accept a percentage unit.

### Aggregate validation

A reported total is not overwritten by a computed total.

### Provenance validation

A derived value has resolvable input observation IDs and formula.

### Mapping validation

`EXACT` mappings require stronger evidence than lexical similarity.

### Unknown-state validation

`UNKNOWN`, `missing`, `not applicable`, `undisclosed`, and zero are
distinct.

------------------------------------------------------------------------

# 33. Synonyms still have a role

A lexical alias index is useful for search:

``` yaml
aliases:
  - "Loans to customers"
  - "Customer loans"
  - "Loans and advances to customers"
```

But aliases should point to **candidate concepts**, not automatically
assert equivalence.

A search index may say:

``` text
"customer loans" -> candidates:
  - concept A
  - concept B
```

The actual mapping depends on source context.

------------------------------------------------------------------------

# 34. Multilingual terminology

Because source reports may be Russian or English, do not use translation
as semantic normalization.

Store:

``` text
source_label
source_language
```

Canonical registry may use English as the primary label and optionally
Russian labels:

``` yaml
labels:
  en: Loans and advances to customers
  ru: Кредиты и авансы клиентам
```

But the Russian canonical label is a translation resource, not a
replacement for the literal Russian source wording.

Two different Russian source phrases can map to the same concept while
remaining distinct source labels.

------------------------------------------------------------------------

# 35. "Same metric" should be decomposed into explicit tests

Before declaring two observations comparable, test:

1.  Same base accounting concept?
2.  Same reporting perimeter?
3.  Same period type and period?
4.  Same measurement basis?
5.  Same gross/net basis?
6.  Same counterparty population?
7.  Same product/instrument scope?
8.  Same currency/unit semantics?
9.  Same treatment of accrued interest?
10. Same impairment treatment?
11. Same accounting-policy regime?
12. Same segment/geography definition where relevant?
13. Same reported/derived status?

Only after these tests can a bridge claim comparability.

------------------------------------------------------------------------

# 36. A practical equivalence model

Instead of one `same_as`, use relations:

``` text
exactMatch
closeMatch
broaderThan
narrowerThan
componentOf
aggregateOf
reconcilesTo
presentationAliasOf
translatedLabelOf
derivedFrom
reclassifiedFrom
restatedFrom
```

This is substantially more expressive and prevents false equivalence.

For example:

``` text
"Loans and advances to customers, net"
narrower/broader relationship depending on canonical perimeter
```

or:

``` text
"Net interest income"
aggregateOf:
  interest income
  interest expense
```

when supported by the source.

------------------------------------------------------------------------

# 37. The role of calculation relationships

IFRS taxonomy calculation relationships can help establish expected
mathematical structure.

Tabularium can use them as:

-   validation hints;
-   candidate aggregate relationships;
-   reconciliation checks.

But they should not become automatic derivation rules for all reports.

A source may present a subtotal with issuer-specific components or
presentation choices. The reported subtotal remains authoritative as a
reported observation.

------------------------------------------------------------------------

# 38. The role of presentation relationships

Presentation hierarchy is useful but should not be mistaken for
accounting ontology.

A child displayed beneath a parent may indicate presentation grouping,
not necessarily a mathematically additive relationship.

Therefore store separately:

``` text
presentation_parent
calculation_parent
semantic_broader_concept
```

These relationships can coincide, but need not.

------------------------------------------------------------------------

# 39. The role of documentation labels

The IFRS Taxonomy's documentation labels are especially valuable for
disambiguation.

The standard label answers roughly:

> What is this concept called?

The documentation label helps answer:

> What does this concept mean?

For mapping, meaning is more important than surface wording.

Therefore candidate matching should weight:

1.  documentation/reference meaning;
2.  dimensional context;
3.  statement/note context;
4.  standard label;
5.  lexical similarity.

Not the reverse.

------------------------------------------------------------------------

# 40. What not to do

## Do not create one giant flat `metrics.csv`

It will quickly become a synonym list with hidden semantic conflicts.

## Do not rename raw Markdown rows

That destroys source fidelity.

## Do not choose one bank's terminology as the standard

Issuer terminology is not IFRS itself.

## Do not assume IFRS taxonomy covers every useful issuer disclosure

Extensions are normal.

## Do not create a new concept for every textual variant

Use source labels + mappings.

## Do not put every qualifier into the concept ID

Use dimensions.

## Do not dimensionalize everything blindly

Some qualifiers alter the underlying construct and deserve separate
concepts.

## Do not infer missing dimensions

Use `UNKNOWN`.

## Do not convert source-specific segment definitions into common segments without a bridge

IFRS 8 segments are entity-specific.

## Do not treat arithmetic reproducibility as semantic proof

`A + B = C` does not prove that C has the economic meaning you assumed.

------------------------------------------------------------------------

# 41. Recommended decision tree for every new source label

``` text
1. Is the source label already mapped in the same semantic context?
   ├─ yes -> reuse mapping, validate context
   └─ no
      ↓
2. Is there an IFRS Taxonomy element with the same accounting meaning?
   ├─ yes -> map to IFRS element
   └─ no
      ↓
3. Can the disclosure be represented by an IFRS base concept + axes/members?
   ├─ yes -> use compositional mapping
   └─ no
      ↓
4. Is there an existing Tabularium concept with the same defined meaning?
   ├─ yes -> map with evidence
   └─ no
      ↓
5. Is this genuinely issuer-specific?
   ├─ yes -> create issuer-specific concept
   └─ uncertain -> AMBIGUOUS / UNMAPPED
```

Never force step 5 into step 2 merely to maximize coverage.

------------------------------------------------------------------------

# 42. Proposed governance

A canonical terminology system needs governance because mappings can
alter comparability.

Recommended states for registry entries:

``` text
DRAFT
REVIEWED
STABLE
DEPRECATED
```

For mappings:

``` text
PROPOSED
REVIEWED
CONFIRMED
DISPUTED
SUPERSEDED
```

Every semantic change should record:

-   previous version;
-   new version;
-   reason;
-   affected observations;
-   whether historical mappings change;
-   whether only display wording changed.

Changing a label without changing meaning is different from changing the
concept definition.

------------------------------------------------------------------------

# 43. Recommended pilot

Do not start with all IFRS notes.

Use a bounded pilot across the existing banking corpus.

Suggested domains:

1.  statement of financial position;
2.  statement of profit or loss;
3.  loans and ECL;
4.  customer funds;
5.  securities;
6.  fee and commission income/expense.

Why these?

They contain nearly every hard problem:

-   synonyms;
-   gross/net;
-   measurement categories;
-   counterparties;
-   products;
-   stages;
-   aggregates;
-   reported subtotals;
-   issuer-specific groupings;
-   cross-bank comparability.

A successful model here will generalize much better than a taxonomy
designed abstractly.

------------------------------------------------------------------------

# 44. Pilot outputs

The pilot should produce actual evidence, not architecture alone.

Recommended outputs:

``` text
concept-registry
dimension-registry
source-label-index
mapping-table
unmapped-queue
ambiguity-register
validation-report
taxonomy-version-map
```

And quantitative diagnostics:

``` text
number of unique source labels
% exact IFRS taxonomy mappings
% compositional IFRS mappings
% Tabularium concepts
% issuer-specific concepts
% ambiguous/unmapped
number of mapping conflicts
number of reused concepts across issuers
```

These metrics reveal whether the model is actually reducing semantic
fragmentation.

------------------------------------------------------------------------

# 45. A stronger long-term model: semantic signature

For machine comparison, each observation can expose a normalized
semantic signature.

Conceptually:

``` text
signature =
  concept
  + reporting_perimeter
  + measurement_basis
  + gross_net_basis
  + counterparty
  + product
  + stage
  + geography
  + segment
  + period_type
  + unit_type
```

Two observations can be candidate-comparable when their signatures match
on all dimensions material to that concept.

This is far stronger than matching `metric_name`.

The signature should not necessarily be serialized into one string; it
is better as structured fields.

------------------------------------------------------------------------

# 46. Distinguish ontology from source schema

There are two useful structures:

## Source schema

What this issuer actually published:

``` text
Note 12
  Loans
    Corporate
    Retail
      Mortgage
      Consumer
```

## Canonical semantic model

How Tabularium describes the meaning:

``` text
concept = loans
counterparty = ...
product = ...
```

Both should survive.

The source schema is evidence. The canonical model is an
interpretation/bridge.

Do not replace one with the other.

------------------------------------------------------------------------

# 47. Relationship to raw Markdown

The raw/source-faithful Markdown work already done remains valuable.

It should continue to preserve:

-   page markers;
-   headings;
-   source tables;
-   row labels;
-   column labels;
-   notes;
-   units;
-   footnotes;
-   order;
-   literal numbers.

The canonical terminology layer should point back to precise source
locations.

Example:

``` yaml
source_locator:
  artifact: ...
  page: 87
  heading: "Note 14. Loans and advances to customers"
  table: 2
  row: "Corporate loans"
  column: "30 June 2026"
```

This makes the semantic mapping auditable.

------------------------------------------------------------------------

# 48. Source locator should be stable enough for regeneration

Page number alone is not enough.

Prefer a compound locator:

``` text
artifact ID
page
section/note
table
row
column
optional source text hash
```

If Markdown rendering changes slightly, the mapping can still be
recovered.

A source-text hash can help detect accidental mutation of mapped text.

------------------------------------------------------------------------

# 49. How to treat restatements

A restated comparative is a new source observation/version, not a silent
replacement of the old observation.

Recommended relationship:

``` text
restatedFrom
```

Keep:

-   originally reported value;
-   restated value;
-   publication that performed the restatement;
-   reason if disclosed;
-   period to which both refer.

Canonical naming must not erase this temporal provenance.

------------------------------------------------------------------------

# 50. How to treat reclassifications

A reclassification may preserve total value while changing categories.

Therefore:

``` text
reclassifiedFrom
```

is different from:

``` text
restatedFrom
```

and both differ from a new-period observation.

This is especially important for long time series.

------------------------------------------------------------------------

# 51. How to treat "other"

`Other` is never globally meaningful.

Correct representation requires its parent context:

``` text
Other assets
Other liabilities
Other operating income
Other operating expenses
Other financial assets
```

A member simply called:

``` text
Other
```

without axis/parent is semantically unsafe.

------------------------------------------------------------------------

# 52. How to treat totals

`Total` is likewise contextual.

Never store:

``` text
concept = Total
```

Instead:

``` text
concept = LoansAndAdvances
aggregation_member = Total
```

or a reported subtotal concept when IFRS meaning requires one.

The word `total` is a presentation role, not a standalone economic
construct.

------------------------------------------------------------------------

# 53. How to treat percentages and ratios

Ratios can be:

-   directly reported;
-   management-defined;
-   regulatory;
-   derived.

Do not map all `NIM`, `ROE`, `cost-to-income`, `capital adequacy`
metrics into generic ratio names without formula and perimeter.

For a ratio, the semantic definition should include:

``` text
numerator construct
denominator construct
averaging convention
annualisation
period
perimeter
adjustments
reported/derived status
```

A reported ratio and a reproducible Tabularium ratio can coexist and
differ legitimately.

------------------------------------------------------------------------

# 54. Regulatory capital is not ordinary IFRS terminology

Banks often include regulatory capital/liquidity information alongside
IFRS reporting.

Examples:

-   CET1;
-   Tier 1;
-   total capital;
-   RWA;
-   LCR;
-   NSFR.

These concepts derive from prudential regulation, not merely IFRS
accounting.

Therefore the semantic registry should support multiple authoritative
namespaces, for example:

``` text
ifrs:
prudential:
tab:
issuer:
```

Do not falsely label regulatory concepts as IFRS concepts merely because
they appear inside an IFRS report.

------------------------------------------------------------------------

# 55. The registry is a graph, not a dictionary

The final conceptual model is closer to a graph:

``` text
source label
  ↓ observed as
source concept
  ↓ exact/broader/narrower/related
canonical concept
  ↔ dimensions
  ↔ members
  ↔ IFRS taxonomy element
  ↔ authoritative references
  ↔ aggregates/components
  ↔ translations
  ↔ previous taxonomy versions
  ↔ issuer-specific extensions
```

This graph structure is what allows machine reasoning without destroying
provenance.

A flat glossary cannot do this.

------------------------------------------------------------------------

# 56. Recommended core invariant

The most important invariant for Tabularium should be:

> **Canonicalization may add a mapping; it may never overwrite what the
> source said.**

A second invariant:

> **Every canonical observation must resolve backwards to the literal
> source observation and the evidence supporting its mapping.**

A third:

> **Every derivation must resolve backwards to its input observations
> and formula.**

These three invariants preserve the source-faithful contract while still
enabling serious cross-report analysis.

------------------------------------------------------------------------

# 57. Final architecture recommendation

For IFRS terminology, adopt the following hierarchy of authority:

``` text
1. Literal source wording
2. Official digital tag from the source filing, where available
3. IFRS Accounting Taxonomy concept/dimension
4. Tabularium canonical concept/dimension
5. Issuer-specific concept
6. Explicit bridge between concepts
7. Derived analytical construct
```

The order is not a ranking of "truth"; it is a provenance chain.

The practical target is:

``` text
SOURCE
  publication + literal label + literal value
       ↓
REPRESENTATION
  source-faithful Markdown/native digital artifact
       ↓
OBSERVATION
  atomic fact + context + locator
       ↓
SEMANTIC MAPPING
  IFRS/Tabularium concept + dimensions + mapping status
       ↓
BRIDGE
  explicit comparability/reconciliation/transformation
       ↓
DERIVATION / ANALYTICAL CLAIM
```

That gives Tabularium a common language without turning the corpus into
a normalized database that pretends the original disclosures were more
uniform than they actually were.

------------------------------------------------------------------------

# 58. Concrete recommendation for the next implementation step

The next step should **not** be to manually invent a complete unified
list of thousands of IFRS indicators.

The next step should be a **terminology discovery pilot** over the
existing IFRS banking corpus:

1.  enumerate literal row/column labels;
2.  attach source locations and structural context;
3.  match them against IFRS Accounting Taxonomy 2025;
4.  identify dimensions and members;
5.  classify mappings as
    `EXACT/BROADER/NARROWER/RELATED/COMPOSITE/SOURCE_SPECIFIC/AMBIGUOUS/UNMAPPED`;
6.  build the first registry only from concepts actually encountered;
7.  test it on several banks;
8.  keep raw Markdown untouched;
9.  quantify conflicts and unmapped cases;
10. only then freeze a v0.1 semantic contract.

This approach is slower for the first hundred concepts and dramatically
safer for the next ten thousand.

------------------------------------------------------------------------

# 59. Proposed v0.1 contract in one block

``` yaml
semantic_contract:
  principles:
    - source_label_is_immutable
    - concept_identity_is_not_label_identity
    - dimensions_are_not_concatenated_into_metric_names
    - reported_is_not_derived
    - missing_is_not_zero
    - unknown_is_not_false
    - source_specific_is_valid
    - mappings_are_versioned
    - every_mapping_has_provenance
    - every_derivation_resolves_to_inputs

  namespaces:
    - ifrs
    - tab
    - issuer
    - prudential

  mapping_relations:
    - EXACT
    - BROADER
    - NARROWER
    - RELATED
    - COMPOSITE
    - SOURCE_SPECIFIC
    - AMBIGUOUS
    - UNMAPPED

  first_dimensions:
    - reporting_perimeter
    - period
    - currency
    - scale
    - measurement_category
    - gross_net_basis
    - counterparty_class
    - product_class
    - credit_risk_stage
    - instrument_class
    - maturity_bucket
    - geography
    - segment

  provenance_classes:
    - reported
    - derived
    - adjusted

  null_states:
    - missing
    - unknown
    - not_applicable
    - undisclosed
```

------------------------------------------------------------------------

# 60. Bottom line

There **is** a strong official foundation for unified IFRS terminology,
but it is not a single mandatory list of financial-statement row names.
The correct foundation is the **IFRS Accounting Taxonomy plus IFRS
presentation/disclosure semantics**, extended by explicit
entity-specific and Tabularium-specific concepts where necessary.

The key architectural move is to stop thinking of a metric as a name.

A financial observation is closer to:

``` text
accounting concept
× reporting perimeter
× period
× unit
× measurement basis
× dimensions
× provenance/status
× source version
```

The name is only one representation of that object.

For Tabularium, therefore, the desirable end state is not "all reports
use the same wording." It is:

> **all source wording remains intact, while semantically comparable
> observations can be addressed through stable canonical concepts,
> explicit dimensions and auditable mappings.**

That is the point at which the corpus becomes genuinely reusable by
humans, AI and software without sacrificing the evidence layer.

------------------------------------------------------------------------

# Primary references

1.  IFRS Foundation --- IFRS Accounting Taxonomy\
    https://www.ifrs.org/issued-standards/ifrs-taxonomy/

2.  IFRS Foundation --- IFRS Accounting Taxonomy 2025\
    https://www.ifrs.org/issued-standards/ifrs-taxonomy/ifrs-accounting-taxonomy-2025/

3.  IFRS Foundation --- IFRS Accounting Taxonomy 2025 to remain current
    for 2026 reporting\
    https://www.ifrs.org/news-and-events/news/2026/02/ifrs-accounting-taxonomy-2025-to-remain-current-for-2026/

4.  IFRS Foundation --- IFRS Taxonomy content terminology\
    https://www.ifrs.org/-/media/feature/standards/taxonomy/general-resources/ifrs-taxonomy-terminology.pdf

5.  IFRS Foundation --- IFRS Taxonomy Architecture\
    https://www.ifrs.org/issued-standards/ifrs-taxonomy/ifrs-taxonomy-architecture/

6.  IFRS Foundation --- IFRS Taxonomy Illustrated\
    https://www.ifrs.org/issued-standards/ifrs-taxonomy/ifrs-taxonomy-illustrated/

7.  IFRS Foundation --- IFRS 18 Presentation and Disclosure in Financial
    Statements, 2026 issued standards\
    https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2026/issued/part-a/ifrs-18-presentation-and-disclosure-in-financial-statements.pdf

8.  IFRS Foundation --- IFRS 18 key terms\
    https://www.ifrs.org/supporting-implementation/supporting-materials-by-ifrs-standards/ifrs-18/key-terms/

9.  IFRS Foundation --- Using the IFRS digital taxonomies: guidance on
    entity-specific extensions\
    https://www.ifrs.org/content/dam/ifrs/about-us/legal-and-governance/legal-docs/taxonomy/taxonomy-legal.pdf

10. ESMA --- ESEF Taxonomy\
    https://www.esma.europa.eu/electronic-reporting/esef-taxonomy
