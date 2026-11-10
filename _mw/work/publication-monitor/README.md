# Publication monitor pilot

This service checks **byte-level changes** in official XLSX files and sends a notification to a private Telegram group. It does **not** ingest source publications into `scrolls/`, determine release periods, parse workbook values, or claim that a change represents revised statistics.

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
