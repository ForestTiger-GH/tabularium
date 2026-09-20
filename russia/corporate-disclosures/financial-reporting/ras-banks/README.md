# RAS Banks — Bank of Russia Regulatory Reporting Bridges

This route documents source-faithful access to high-volume regulatory reporting datasets for Russian credit institutions without mirroring the full Bank of Russia datasets in Git.

## Forms

- [form-0409101/](form-0409101/) — turnover balance sheet by accounting accounts.
- [form-0409102/](form-0409102/) — financial results.
- [form-0409123/](form-0409123/) — own funds (capital), Basel III.
- [form-0409135/](form-0409135/) — mandatory ratios and other performance indicators.

## Model

The Bank of Russia remains the canonical data host. Each form directory contains:

- README.md — scope and source identity;
- AGENTS.md — retrieval and interpretation protocol;
- bridge.yaml — machine-readable endpoints and fallback topology.

The normal path is to use the Bank of Russia public organization/form pages for the main disclosed data. When a request needs deeper granularity, use the documented web-service and bulk-archive fallbacks and verify the disclosure regime applicable to the requested date.

Fallback access is not a bypass around disclosure restrictions. If the Bank of Russia suppresses a row, account, symbol, field, or level of detail for a reporting date, another Bank of Russia channel may expose the same restricted public dataset. Report such cases as disclosure suppression rather than as zero or missing data.
