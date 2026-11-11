"""Offline outbox, failure isolation and commit ordering tests."""
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "_mw/work/publication-monitor"))
sys.path.insert(0, str(ROOT / "scripts"))
import fns_sme_pipeline as p
import capture_fns_sme as fns


def sample_event(key="alpha"):
    return {
        "type": "PUBLISHED_NEW", "event_id": key,
        "observed_at": "2026-11-11T10:00:00Z",
        "reference_date": "2026-11-10",
        "csv_path": "scrolls/russia/authorities/federal-tax-service/sme-registry-statistics/2026/2026-11-10_SME-REG.csv",
        "csv_sha256": "f" * 64, "regions": 89, "changed_regions": 89,
    }


class Journal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "events.jsonl"

    def test_pending_until_acknowledged(self):
        p.events_append([sample_event()], self.path)
        _, items, notified = p.events_read(self.path)
        self.assertEqual(list(items), ["alpha"])
        self.assertFalse(notified)
        p.events_append([{"type": "NOTIFIED", "event_id": "alpha",
                          "notified_at": "2026-11-11T10:01:00Z"}], self.path)
        _, items, notified = p.events_read(self.path)
        self.assertEqual(notified, {"alpha"})

    def test_duplicate_id_and_orphan_ack_fail(self):
        p.events_append([sample_event(), sample_event()], self.path)
        with self.assertRaisesRegex(p.PipelineError, "DUPLICATE_EVENT_ID"):
            p.events_read(self.path)
        self.path.write_text('{"type":"NOTIFIED","event_id":"nope"}\n', encoding="utf-8")
        with self.assertRaisesRegex(p.PipelineError, "ORPHAN_NOTIFICATION"):
            p.events_read(self.path)

    def test_pending_notification_retries_without_touching_data(self):
        p.events_append([sample_event()], self.path)
        with patch.object(p, "EVENTS", self.path), patch.object(p, "relative", return_value="event_path"), \
             patch.object(p, "send_telegram") as sender, \
             patch.object(p, "safe_publish", return_value=True) as publisher, \
             patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "fake", "TELEGRAM_CHAT_ID": "fake"}):
            self.assertEqual(p.flush_outbox(), 0)
            sender.assert_called_once()
            publisher.assert_called_once()
        self.assertEqual(len(p.events_read(self.path)[2]), 1)
        with patch.object(p, "EVENTS", self.path), patch.object(p, "send_telegram") as sender:
            self.assertEqual(p.flush_outbox(), 0)
            sender.assert_not_called()

    def test_failed_send_leaves_pending(self):
        p.events_append([sample_event()], self.path)
        with patch.object(p, "EVENTS", self.path), patch.object(
                p, "send_telegram", side_effect=p.MonitorError("TELEGRAM_REJECTED")), \
                patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "fake", "TELEGRAM_CHAT_ID": "fake"}), \
                patch.object(p, "safe_publish") as publisher:
            self.assertEqual(p.flush_outbox(), 1)
            publisher.assert_not_called()
        self.assertEqual(p.events_read(self.path)[2], set())


class Selection(unittest.TestCase):
    def test_scheduled_checks_latest_and_recent_missing_only(self):
        dates = [date(2026, m, 10) for m in range(1, 11)]
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(p, "REPO", Path(temp)):
                # No files: select recent eight months, never the entire archive.
                self.assertEqual(p.select_dates(dates, mode="check"), dates[-8:])
                for d in dates[-8:-2]:
                    dest = fns.file_for(d, Path(temp) / fns.CORPUS)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(b"placeholder")
                self.assertEqual(p.select_dates(dates, mode="check"), dates[-2:])

    def test_backfill_bounded_and_only_published_dates(self):
        dates = [date(2026, m, 10) for m in range(1, 12)]
        self.assertEqual(
            p.select_dates(dates, mode="backfill", from_date="2026-02-10", to_date="2026-03-10"),
            dates[1:3])
        with self.assertRaisesRegex(p.PipelineError, "BACKFILL_RANGE_REQUIRED"):
            p.select_dates(dates, mode="backfill")


class Lifecycle(unittest.TestCase):
    def test_dry_run_never_publishes_or_notifies(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(p, "REPO", Path(temp)), \
                 patch.object(p.source, "discover_dates", return_value=[date(2026, 10, 10), date(2026, 11, 10)]), \
                 patch.object(p.source, "capture", return_value=(self.csv_bytes(), "a"*64)), \
                 patch.object(p, "safe_publish") as push, \
                 patch.object(p, "flush_outbox") as notify:
                self.assertEqual(p.process("dry-run"), 0)
                push.assert_not_called()
                notify.assert_not_called()

    def csv_bytes(self):
        rows = {str(i).zfill(2): (str(i).zfill(2), f"Region {i}", "10",
                              "2", "1", "0", "7", "0", "0")
                for i in range(1, 90)}
        return fns.write_csv(rows)

    def test_push_is_before_notification(self):
        order = []
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            journal = base / "events.jsonl"
            with patch.object(p, "REPO", base), patch.object(p, "EVENTS", journal), \
                 patch.object(p, "relative", side_effect=lambda x: str(x)), \
                 patch.object(p.source, "discover_dates", return_value=[date(2026, 10, 10), date(2026, 11, 10)]), \
                 patch.object(p.source, "capture", return_value=(self.csv_bytes(), "a"*64)), \
                 patch.object(p, "safe_publish", side_effect=lambda *a, **kw: order.append("push") or True), \
                 patch.object(p, "flush_outbox", side_effect=lambda *a, **kw: order.append("notify") or 0), \
                 patch.object(p, "cmd", return_value=Mock(stdout="f" * 40)):
                self.assertEqual(p.process("check"), 0)
                self.assertEqual(order, ["notify", "push", "notify"])
                self.assertEqual(len(p.events_read(journal)[1]), 2)
                self.assertEqual(len(list((base / fns.CORPUS).glob("*/*.csv"))), 2)


if __name__ == "__main__":
    unittest.main()
