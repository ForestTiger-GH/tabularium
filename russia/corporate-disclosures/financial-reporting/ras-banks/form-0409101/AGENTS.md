# AGENTS.md

## Form model

Form 0409101 is account-based regulatory reporting.

For a source observation preserve at least:
- reporting date;
- Bank of Russia registration number;
- source account or source-defined aggregate code;
- active/passive side where applicable;
- source field or measure;
- unit;
- reported value.

Account codes are identifiers, not decimal numbers.

Never merge active and passive observations that share an account code.

## Main access

Use the official Bank of Russia HTML form for the main publicly disclosed data when accessible:
https://www.cbr.ru/banking_sector/credit/coinfo/f101?dt={date}&regnum={regnum}

Use the institution reporting index to verify availability:
https://www.cbr.ru/finorg/foinfo/reports/?ogrn={ogrn}

## Deep-detail fallback

If the requested account granularity or field is not present in the HTML form:

1. Check the disclosure regime for the reporting date.
2. If the detail is permitted but the HTML view is insufficient, use the CreditOrgInfo web-service operations in bridge.yaml.
3. If needed, use the official bulk DBF archive and the date-effective format description.
4. If public disclosure suppresses the requested detail, return suppressed. Do not infer second-order accounts from a first-order aggregate.

Fallback channels may expose the same restricted public dataset and therefore do not guarantee deeper detail.

## 2026 disclosure snapshot

For reports from 1 January through 1 December 2026, the Bank of Russia publishes only columns 1, 6, and 21 and generally aggregates account information to first-order accounts separately for active and passive accounts. The decision also requires additional combinations of selected first-order accounts into source-defined aggregates, while accounts 99996-99999 remain unaggregated.

Official decision:
https://www.cbr.ru/rbr/dir_decisions/rsd_2025-12-19_23_02/

Treat this as a 2026 rule only.

## Interpretation guardrails

- Preserve opening and closing balances as distinct source fields.
- Do not treat a missing second-order account as zero.
- Preserve source-defined aggregates exactly as published.
- Do not silently expand an aggregate into undisclosed components.
- When the user requests an analytical aggregate, first identify the exact published source rows, then perform the analytical calculation outside this source layer.
