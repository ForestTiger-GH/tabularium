# Banking service network

Separate source-faithful banking-office series with different observation units and date semantics.

## Routes

- [`bank-regional-offices/`](bank-regional-offices/) — dated bank-by-territory office observations.
- [`territorial-offices/`](territorial-offices/) — monthly official territorial aggregates and office categories.

Do not join or harmonize them within this source observation layer, or infer bank-specific values from territorial aggregates.
