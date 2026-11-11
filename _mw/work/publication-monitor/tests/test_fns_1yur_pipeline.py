"""Offline operational outbox, failure isolation and workflow wiring tests for 1-YUR."""
from datetime import date
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "_mw/work/publication-monitor"))
sys.path.insert(0, str(ROOT / "scripts"))
import fns_1yur_pipeline as p
import capture_fns_1yur as source


def event(ident="one"):
    return {
        "type": "PUBLISHED_NEW", "event_id": ident,
        "reference_date": "2026-11-01", "regions": 88,
        "legal_kinds": 37, "changed_regions": 88,
        "csv_path": source.file_for(date(2026, 11, 1)).as_posix(),
        "csv_sha256": "f" * 64,
    }


class Outbox(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = Path(self.tmp.name) / "events.jsonl"

    def test_pending_and_ack_events(self):
        p.append_events([event()], self.log)
        _, published, ack = p.events_read(self.log)
        self.assertEqual(set(published), {"one"})
        self.assertFalse(ack)
        p.append_events([{"type": "NOTIFIED", "event_id": "one",
                          "notified_at": "2026-11-11T10:00:00Z"}], self.log)
        self.assertEqual(p.events_read(self.log)[2], {"one"})

    def test_corrupt_or_orphan_ack_rejected(self):
        p.append_events([{"type": "NOTIFIED", "event_id": "unknown"}], self.log)
        with self.assertRaisesRegex(p.PipelineError, "ORPHAN_OUTBOX_ACK"):
            p.events_read(self.log)
        self.log.write_text("{not json}\n", encoding="utf-8")
        with self.assertRaisesRegex(p.PipelineError, "OUTBOX_CORRUPT"):
            p.events_read(self.log)

    def test_format_alert_links_real_corpus_path(self):
        msg = p.alert(event())
        self.assertIn("2026-11-01_1-YUR.csv", msg)
        self.assertIn("ФНС 1-ЮР", msg)


class Scheduling(unittest.TestCase):
    def test_backfill_bounded_and_explicit(self):
        available = [date(2026, i, 1) for i in range(1, 12)]
        self.assertEqual(p.choose_dates(available, "backfill",
                                        "2026-03-01", "2026-04-01"), available[2:4])
        with self.assertRaisesRegex(p.PipelineError, "BACKFILL_RANGE_REQUIRED"):
            p.choose_dates(available, "backfill")
        with self.assertRaisesRegex(p.PipelineError, "BACKFILL_RANGE_REVERSED"):
            p.choose_dates(available, "backfill",
                           "2026-05-01", "2026-04-01")

    def test_check_does_not_download_entire_history(self):
        dates = [date(2026, m, 1) for m in range(1, 12)]
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(p, "REPO", Path(temp)):
                selected = p.choose_dates(dates, "check")
                self.assertLessEqual(len(selected), 9)
                self.assertEqual(selected[-1], date(2026, 11, 1))

    def test_one_workflow_and_old_manual_modes_preserved(self):
        flow = (ROOT / ".github/workflows/publication-monitor.yml").read_text(encoding="utf-8")
        for cron in ("0 1 * * *", "48 5 * * *", "36 10 * * *",
                     "24 15 * * *", "12 20 * * *"):
            self.assertIn(cron, flow)
        self.assertEqual(flow.count("- cron:"), 5)
        for mode in ("fns-backfill", "fns-dry-run", "fns-verify",
                     "fns-1yur-backfill", "fns-1yur-dry-run", "fns-1yur-verify"):
            self.assertIn(mode, flow)
        self.assertIn("queue: single", flow)
        self.assertIn("cancel-in-progress: false", flow)
        self.assertIn("github.event.repository.private == false", flow)
        self.assertIn("needs: fns-sme", flow)
        self.assertIn("\n  fns-1yur:\n    needs: fns-sme", flow)
        self.assertNotIn("\nfns-1yur:\n", flow)


class Lifecycle(unittest.TestCase):
    def test_dry_run_never_commits_or_sends(self):
        day = date(2026, 11, 1)
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(p, "REPO", Path(temp)), \
                 patch.object(source, "discover", return_value={
                     day: ("https://www.nalog.gov.ru/page", "https://www.nalog.gov.ru/test.zip")}), \
                 patch.object(source, "capture", return_value=(b"sample", {})), \
                 patch.object(source, "compare", return_value=("NEW", 88)), \
                 patch.object(p, "safe_publish") as publisher, \
                 patch.object(p, "flush_outbox") as notify:
                self.assertEqual(p.process("dry-run"), 0)
                publisher.assert_not_called()
                notify.assert_not_called()

    def test_invalid_source_cannot_replace_existing_csv(self):
        day = date(2026, 11, 1)
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(p, "REPO", Path(temp)), \
                 patch.object(source, "discover", return_value={
                     day: ("https://www.nalog.gov.ru/page", "https://www.nalog.gov.ru/test.zip")}), \
                 patch.object(source, "capture", side_effect=source.SourceError("XLS_NOT_OLE")), \
                 patch.object(p, "safe_publish") as publisher:
                self.assertEqual(p.process("dry-run"), 1)
                publisher.assert_not_called()

    def test_publication_outbox_only_after_csv_is_staged(self):
        day = date(2026, 11, 1)
        fake = b"csv-payload"
        meta = {"archive_url": "https://www.nalog.gov.ru/a.zip",
                "archive_sha256": "a" * 64, "member_name": "one.xls",
                "member_sha256": "b" * 64, "regions": 88, "legal_kinds": 37}
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            order = []
            def published(paths, message):
                target = base / source.file_for(day)
                self.assertTrue(target.is_file())
                self.assertEqual(target.read_bytes(), fake)
                order.append("push")
                return True
            with patch.object(p, "REPO", base), \
                 patch.object(source, "discover", return_value={
                     day: ("https://www.nalog.gov.ru/page", "https://www.nalog.gov.ru/test.zip")}), \
                 patch.object(source, "capture", return_value=(fake, meta)), \
                 patch.object(source, "compare", return_value=("NEW", 88)), \
                 patch.object(p, "append_events") as log, \
                 patch.object(p, "relative", side_effect=lambda path: str(path)), \
                 patch.object(p, "safe_publish", side_effect=published), \
                 patch.object(p, "flush_outbox", side_effect=lambda: order.append("notify")), \
                 patch.object(p, "git", return_value=Mock(stdout="cafe")):
                self.assertEqual(p.process("check"), 0)
                self.assertEqual(order, ["notify", "push", "notify"])
                log.assert_called_once()


if __name__ == "__main__":
    unittest.main()
