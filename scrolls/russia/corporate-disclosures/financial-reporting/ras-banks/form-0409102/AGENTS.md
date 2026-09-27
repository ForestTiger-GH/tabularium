# AGENTS.md

## Form model

Form 0409102 is a period financial-results form organized by parts, sections, rows, and symbols.

Preserve:
- institution identifier;
- reporting issue date;
- the actual reporting-period boundaries stated by the source;
- part, section, row, and symbol identifiers;
- unit;
- reported value.

Symbol codes are identifiers. Preserve leading zeroes.

## Main access

Use the official Bank of Russia HTML form for the main disclosed data when accessible:
https://www.cbr.ru/banking_sector/credit/coinfo/f102?dt={date}&regnum={regnum}

Use the institution reporting index to verify availability:
https://www.cbr.ru/finorg/foinfo/reports/?ogrn={ogrn}

The URL date identifies the report issue. Read the actual reporting period from the form itself. Do not assume that the URL date is the economic period.

## Deep-detail fallback

When the public HTML presentation does not expose the requested symbol or level of detail:

1. Check the date-effective disclosure regime.
2. Use Form102IndicatorsEnumXML to resolve source symbols where useful.
3. Use Data102FormXML or other documented form-102 operations where the runtime supports SOAP.
4. Use the official bulk DBF publication and date-effective format description when necessary.
5. If disclosure rules suppress the requested symbol, return suppressed.

## 2026 disclosure snapshot

For 2026, the Bank of Russia publishes columns 1, 2, 3, and 6 for a restricted set consisting mainly of section totals, specified aggregate combinations, totals for major parts, and selected symbols including 01000, 02000, 03000, 04000, 61101, 61102, 40000, 50000, 81101, 81102, 81201, and 81202.

Official decision:
https://www.cbr.ru/rbr/dir_decisions/rsd_2025-12-19_23_02/

Treat this as a 2026 rule only.

## Interpretation guardrails

- Never add cumulative periods together.
- To derive a standalone quarter from cumulative reports, subtract compatible cumulative periods only in analytical work.
- Keep the directly reported source value distinct from any derived quarter value.
- Do not infer a missing detailed symbol from a section total.
