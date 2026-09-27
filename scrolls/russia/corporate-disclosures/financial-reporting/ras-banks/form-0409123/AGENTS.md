# AGENTS.md

## Form model

Form 0409123 is a point-in-time regulatory capital calculation organized by source row codes.

Preserve:
- reporting date;
- institution identifier;
- row code;
- row label;
- unit;
- reported value.

Row codes are strings. Preserve leading zeroes, especially row 000.

## Main access

Use the institution reporting index to confirm that form 0409123 exists for the institution and date:
https://www.cbr.ru/finorg/foinfo/reports/?ogrn={ogrn}

Follow the official form link when the runtime can read the human-facing report.

For structured retrieval, use Data123FormFullXML from the Bank of Russia CreditOrgInfo service.

## Deep-detail fallback

If a requested capital component is not visible:

1. Check the disclosure regime for the reporting date.
2. Use Data123FormFullXML and GetDatesForF123.
3. Use the official bulk DBF archive and the date-effective format description if the runtime supports it.
4. If the row is suppressed for that date, return suppressed rather than deriving it from disclosed totals.

## 2026 disclosure snapshot

For reports from 1 January through 1 December 2026, the Bank of Russia public disclosure is limited to:
- 000 — own funds (capital), total;
- 102 — base capital, total;
- 105 — additional Tier 1 capital, total;
- 203 — supplementary capital, total.

Official decision:
https://www.cbr.ru/rbr/dir_decisions/rsd_2025-12-19_23_02/

Treat this as a 2026 rule only.

## Interpretation guardrails

- Preserve source row codes exactly.
- Do not reconstruct undisclosed capital components from disclosed totals unless the user explicitly requests an analytical derivation and the arithmetic is fully identified as derived.
- Use the form version and definitions effective on the reporting date when interpreting historical rows.
