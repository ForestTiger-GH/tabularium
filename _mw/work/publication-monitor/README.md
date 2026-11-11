# Publication monitor pilot

The XLSX watcher checks **byte-level changes** in official files and sends a notification to a private Telegram group. The separate FNS pipelines publish source-extracted observations into `flakes/`. The XLSX watcher does not ingest source publications, determine release periods, parse workbook values, or claim that a byte change represents revised statistics.

The versioned `registry.json` contains 41 fixed Bank of Russia links and three Ministry of Finance attachment identities. These are independent local configuration records. `state.json` holds only the last successfully baselined or notified SHA-256 per source; it is operational state, not primary-source evidence. Rosstat is not configured.

## Operations

From the repository root, using Python 3.12+ and the standard library:

```bash
python _mw/work/publication-monitor/monitor.py validate
python -m unittest discover -s _mw/work/publication-monitor/tests -p 'test_*.py' -q
python _mw/work/publication-monitor/monitor.py check --dry-run
python _mw/work/publication-monitor/monitor.py bootstrap
```

`bootstrap` silently records a first valid checksum **only for IDs without a checkpoint**. A failed or unavailable source remains unbaselined and is retried later. `check --dry-run` has no network-side Telegram effects and does not modify checkpoints. A normal `check` requires `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in the environment; `TELEGRAM_THREAD_ID` is optional. A first-seen source creates a silent baseline. Later byte changes produce messages; successful delivery is verified before a checkpoint advances. The one-time `test-telegram` mode sends a clearly marked test message.

The private group chat ID and bot token **must** be provided as GitHub Actions repository secrets, never checked into this public repository. The optional topic ID may be an Actions variable. Set up the bot in the intended private group with permission to post messages; there is no webhook or server requirement.

## GitHub Actions lifecycle

`.github/workflows/publication-monitor.yml` is an **operational experimental pilot**, activated after validating Telegram and official publisher access. It checks five times daily at **01:00, 05:48, 10:36, 15:24, and 20:12 UTC**, spaced 4 hours and 48 minutes apart. At a fixed UTC+03 offset, that corresponds to **04:00, 08:48, 13:36, 18:24, and 23:12**. The workflow does not follow Finnish daylight-saving transitions: actual Helsinki clock time is one hour earlier during Finnish winter (UTC+02). Scheduled starts are best-effort and may be delayed or dropped; manual `validate`, `dry-run`, `bootstrap`, `check`, and `test-telegram` modes remain available. The pilot remains a service in the non-authoritative engineering workspace, not a source publication or a corpus schema. The existing source-capture workflows are independent and remain unchanged. The job is restricted to the `main` branch of the public Tabularium repository. It runs offline validation first and will only commit changed `state.json` after a `bootstrap` or `check` invocation. It never commits downloaded XLSX files.

The workflow concurrency group has `cancel-in-progress: false` and `queue: single`. This retains one running check and at most one pending check. If a newer check is triggered while both slots are occupied, the older pending run is canceled/replaced; the currently running check continues. Every accepted run scans the registered files even when the previous completed recently. A GitHub-dropped schedule cannot be recovered by the queue.

For a normal check, GitHub stores an updated SHA only after a successful Telegram API response. This provides **at-least-once**, not exactly-once delivery: if Telegram accepts a message and the subsequent Git push fails, the next run may resend it. A push conflict or changed monitor code/registry/state causes failure rather than overwriting concurrent edits. No empty keepalive commits are made.

The Ministry of Finance page, three dynamic attachments, and the CBR XLSX downloads were verified on the intended public GitHub runner on 2026-11-10. All 44 source checks passed, and a subsequent full comparison reported 44 unchanged files with zero errors. Future source availability is not guaranteed; if the publisher changes the page structure, the attachment resolver fails closed. Use manual `dry-run` for diagnostics. Its link resolver deliberately fails if the page contains no match or multiple distinct matches. Source errors are reported in the workflow log and do not advance a hash. Do not assume a date from a URL or filename.

## Adding files

Add a unique ID, human-readable title, official publisher, and approved HTTPS source URL to `registry.json`. `direct` retrieves the given XLSX URL; `page_attachment` resolves one filename pattern on an official HTML page. New publishers require an explicit review of the allowlisted hosts and paths in `monitor.py`. Changes to the monitored source list are deliberate and do not depend on another repository's runtime. Maintain the offline registry-snapshot test for the initial fixed CBR list.

Four registered CBR URLs using `cbr.ru` returned HTTP 403 during the live GitHub-runner baseline on 2026-11-10; the exact same paths on official `www.cbr.ru` returned valid XLSX files. The downloader now retries that host **only** for CBR HTTP 403 on `cbr.ru`. The 41 copied source identities and registered URLs are not rewritten, and only the validated downloaded bytes determine SHA-256.

Publisher endpoints are subject to availability and access controls. A monitoring failure means **unknown source state**, not “no change”. A changed SHA-256 means changed file bytes, not necessarily changed statistical observations.

## Regional SME registry capture

The independent [FNS source adapter](../../../scripts/capture_fns_sme.py) extracts the publisher's dated regional JSON statistics into validated CSV representations. The [FNS operational pipeline](fns_sme_pipeline.py) uses temporary runtime staging, compares actual region-and-indicator observations, and commits an updated monthly CSV together with a compact JSONL publication event in `fns_sme_events.jsonl`. It sends Telegram only after the corpus push succeeds. `NOTIFIED` entries acknowledge delivery; publication events without an acknowledgment remain retryable, including when Telegram is unavailable. The JSONL is an operational outbox, not a history of source values or part of the corpus; no entry is created for an unchanged scan. Each release date keeps only its latest CSV; previous values are not duplicated as revision files.

The existing 44 XLSX checks and their `registry.json` / `state.json` remain independent. Scheduled FNS checks run in the **same** five fixed-UTC workflow slots, in a separate job after the XLSX job. Manual `fns-dry-run`, `fns-verify`, and `fns-backfill` modes act on the FNS stream only; `check` checks both streams. Backfill requires a published-date range and processes at most 15 releases per invocation. Standard-library Python 3.12 is sufficient. Temporary candidate data is neither committed nor uploaded as an artifact. Failed source checks leave existing CSVs untouched.

A successful FNS data publication and its JSONL event are committed together. An outage during Telegram delivery does not roll back the data; the next eligible run retries the pending event. Notification acknowledgment creates its own small commit, and delivery is at-least-once. Source-specific readme: [SME register observations](../../../flakes/organizations/sme-register-population/).

## FNS Form 1-YUR legal-entity regional capture

The source-specific [Form 1-YUR adapter](../../../scripts/capture_fns_1yur.py) and [historical adapter](../../../scripts/capture_fns_1yur_history.py) discover only official FNS release links and select the actual first part of each source publication: modern `(1).xls`, archival `_I.xls` / `_I.xlsx`, or a single unambiguous source workbook. They support the publisher's XLS, RAR, ZIP and OOXML workbooks, including observed misleading file extensions, using the pinned readers in `scripts/requirements_fns_1yur.txt`. Each CSV keeps the original Russia, federal-district and territory rows and original reported numbers, but uses the canonical `le_<measure>__<kind>` field names of the reviewed source-epoch mapping. Only direct identity aliases to the 2026 category constructs are retained. Older source editions use different indicator numbers and legal-kind codes; unmatched fields, unreported measures and registration-record counts are absent (never zero-filled). The single per-date [`field-provenance.json`](../../../flakes/organizations/legal-entity-population/field-provenance.json) records every retained and omitted original field and the pre/post conversion hashes. New snapshots are converted by the same mapper before comparison or Git publication. The [operational job](fns_1yur_pipeline.py) runs after the existing XLSX watcher and SME job, reusing the same five UTC slots and one-active/one-pending workflow queue; it does not redefine or modify the SME register series.

Each new or materially changed CSV is committed together with a 1-YUR publication event in `fns_1yur_events.jsonl` (created upon the first publication), then the independent Telegram outbox sends an event-specific notification and appends a `NOTIFIED` acknowledgment. There are no revisions or unchanged-scan commits. Archive/member hashes, original member filename, date, source URL, parser commit, and CSV hash belong to that event, not to the regional rows. Outbox delivery is at-least-once. An invalid source leaves the existing CSV unchanged. Source-internal disagreements between category and territorial views are recorded as provenance, while the original category-sheet observations remain unchanged. Historical `BASELINE_IMPORTED`, `BASELINE_CORRECTED`, and one-time `SCHEMA_MIGRATED` events are silent and independent of Telegram. Future capture events include source-coded CSV hashes and exact canonical field aliases.

Regular checks inspect only the latest few published dates and bounded recent missing releases. Manual modes `fns-1yur-dry-run`, `fns-1yur-verify`, `fns-1yur-backfill`, and `fns-1yur-check` act only on this source. Backfill uses its **own** `fns_1yur_from_date` / `fns_1yur_to_date` inputs and accepts no more than 15 official linked dates per invocation. For example, `python _mw/work/publication-monitor/fns_1yur_pipeline.py dry-run` checks data without committing or notifying; `python scripts/capture_fns_1yur.py capture --xls path/to/source.xls --date 2026-11-01 --output candidate.csv` provides an offline workbook-to-CSV validation path. A change to historical form layout/classification must be reviewed and supported explicitly before backfill; never fill absent historical codes with zeros.

The source-specific evidence contract and the distinction from SME statistics are documented in [legal-entity observations](../../../flakes/organizations/legal-entity-population/). The old 44-source byte-level register, its checkpoint semantics, and FNS SME's JSON adapter/outbox remain unchanged.
