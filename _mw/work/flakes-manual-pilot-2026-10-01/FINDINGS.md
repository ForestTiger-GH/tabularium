# First manual findings

These are observations from the hands-on pass, not production decisions.

## 1. The name `flakes` works well as a layer/package name

It is short and visually distinct from `scrolls`. More importantly, the pilot suggests that **flake should not become a new epistemic stage**. A package contains different record types; calling every row simply a “flake” would hide whether it is a source observation, assertion, binding, or finding.

## 2. A minimal manual package can be very small

For hands-on work, `manifest.json + flakes.jsonl` is sufficient. Splitting five JSONL files immediately would add friction without yet proving value. The split can be generated later from `record_type`.

## 3. Document-level metadata is not safe to inherit blindly

Two concrete failures appeared immediately:

- Sber’s income statement is labelled “in billions of Russian rubles”, but EPS on the same page is RUB/share.
- ABC’s publication is IFRS, but its disclosed cost-to-income ratio is explicitly **under PRC GAAP**.

Therefore unit, accounting basis, perimeter, and measurement role need record/block overrides.

## 4. “Adjusted” is not a construct

OTP is the strongest example. Page 2 simultaneously contains:

- “Adjusted profit after tax considering the prorated recognition of special items...” = HUF 580,303m;
- “Consolidated adjusted profit after tax” = HUF 482,738m.

Both are source-faithful labels. They must remain distinct until a method/binding explains their relationship. A generic `adjusted=true` flag is insufficient.

## 5. Raw observations should exist before canonical naming

The selected rows were easy to preserve with source label, period/column, literal, unit, and locator. Canonical bindings could then be proposed independently. This feels materially safer than forcing every newly encountered row into a global concept registry during extraction.

## 6. The same text block can yield both assertion and number

OTP’s executive summary contains reported results, normalized/counterfactual methodology, and explanations in the same paragraphs. ABC’s dividend section is an event with quantitative parameters. Numeric and semantic layers should share source blocks and cross-references rather than be treated as mutually exclusive corpora.

## 7. Coverage must be explicit from the first manual pass

All three packages are marked `sampled`. Without this, a large-looking JSONL file could easily be mistaken for a complete extraction. A future “process report” command needs block inventory before it can truthfully say `extraction_complete`.

## 8. Source revision beats path stability

OTP is still in `_mw/_arrivals/`. The pilot remains reproducible because the manifest freezes its Git blob SHA. If the report later moves into `scrolls/` unchanged, that should not create a new economic observation history.

## 9. Suggested next test

Do **one report completely**, page by page, with every block assigned a coverage status and every numeric candidate explained. Sber is large enough to stress the model; ABC (16 pages) is better for the first full-close exercise. I would use ABC first because a complete manual pass is feasible and already contains several semantic traps.

## 10. A residual may be a source-basis bridge, not an error

ABC immediately produced a useful decomposition trap. The headline loan balance is RMB28,482,604m, while the four disclosed business-type components are explicitly **excluding accrued interest** and sum to RMB28,424,118m. The RMB58,486m difference is therefore a bridge/residual caused by different source grain/basis unless separately explained by the source.

The deposit disclosure behaves the same way: headline deposits are RMB34,517,455m; business-line components excluding accrued interest sum to RMB34,076,038m; residual RMB441,417m.

This is exactly why a reproducible subtraction does not by itself justify an economic label for the residual.

