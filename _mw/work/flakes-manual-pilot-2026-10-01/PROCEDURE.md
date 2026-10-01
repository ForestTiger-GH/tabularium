# Manual procedure

This is the hands-on procedure used in the pilot.

## 1. Freeze the source

Record the exact repository path and Git blob SHA. A path alone is not a stable source revision.

## 2. Declare scope before extraction

Choose pages/blocks to process. If the pass is sampled, say so before writing observations. Never infer `complete` from the presence of many records.

## 3. Map source blocks

Create a `block` record with page, line range, title/kind, and processing status. Blocks are locators and coverage units; they are not economic facts.

## 4. Extract numeric observations literally

For every selected numeric item preserve at least:

- source label;
- column/time label;
- literal published value;
- parsed decimal only when unambiguous;
- source unit and scale;
- source-defined dimensions/qualifiers;
- exact source locator;
- reported/adjusted/other role when the source makes the distinction.

Do not require a canonical construct before saving a valid observation.

## 5. Extract semantic assertions separately

Preserve what the source actually says: subject, predicate/action, modality, polarity, time, and literal evidence. A statement containing a number may have both an assertion and a linked numeric observation.

## 6. Add candidate bindings only after raw extraction

Mappings to common concepts are separate `binding` records with `mapping_status=proposed`. A binding may be changed without rewriting the source observation.

## 7. Record awkward cases as findings

Do not fix the source or silently choose an interpretation. Findings are first-class pilot output.

## 8. Re-read the source against the package

Manual review asks two independent questions:

1. Are the written records faithful to the selected source blocks?
2. Did the selected scope omit something structurally important?

## 9. Close coverage honestly

Use `sampled`, `processed_complete`, `unresolved`, or another explicit status. Missing is never zero; unprocessed is never absent.

## 10. Only then discuss derivations

Ratios, currency conversion, aggregations, quarter-from-YTD calculations, and cross-source bridges are a later step. A reproducible calculation still does not prove that the economic interpretation is correct.
