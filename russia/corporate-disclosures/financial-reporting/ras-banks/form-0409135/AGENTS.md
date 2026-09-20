# AGENTS.md

## Form model

Form 0409135 is a point-in-time regulatory-ratio and indicator form with date-sensitive structure and metadata.

Preserve:
- reporting date;
- institution identifier;
- section;
- source indicator or ratio code;
- source label;
- unit;
- reported value.

Preserve the source spelling and characters in ratio codes. In Russian labels, Cyrillic Н and Latin H are not interchangeable source characters.

## Main access

Use the institution reporting index to verify availability:
https://www.cbr.ru/finorg/foinfo/reports/?ogrn={ogrn}

Follow the official form link when available to the runtime.

For structured data, use Data135FormFullXML. For date-effective structure and labels, use Data135MetaFullXML.

## Deep-detail fallback

When a requested ratio or other form-135 indicator is not exposed:

1. Check the disclosure regime for the reporting date.
2. Use GetDatesForF135, Data135FormFullXML, and Data135MetaFullXML.
3. Use the official bulk DBF archive and the corresponding historical format description when required.
4. If the relevant section or indicator is suppressed, return suppressed.

## 2026 disclosure snapshot

For 2026, public disclosure is limited to section 3 mandatory-ratio rows Н1.1, Н1.2, Н1.0, Н1.3, Н2, Н3, Н4, Н15, Н15.1, Н16, Н16.1, Н16.2, Н18, and Н27. The 2026 Bank of Russia decision specifies that Н27 applies starting with reporting as of 1 February 2026.

Official decision:
https://www.cbr.ru/rbr/dir_decisions/rsd_2025-12-19_23_02/

Treat this as a 2026 rule only.

## Interpretation guardrails

- Resolve the form structure against the reporting date before interpreting historical codes.
- Do not assume current section or row meanings apply to old periods.
- Keep ratios, calculated values, and source units exactly as published.
- Do not manufacture a ratio from hidden components when the requested source observation is suppressed.
