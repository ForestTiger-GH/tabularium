"""Offline contract tests; no requests to publishers or Telegram."""
import hashlib
import importlib.util
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("publication_monitor", ROOT / "monitor.py")
monitor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = monitor
spec.loader.exec_module(monitor)


class Headers(dict):
    def get_content_type(self):
        return self.get("Content-Type", "application/octet-stream").split(";")[0]

    def get_content_charset(self):
        return "utf-8"


class Response:
    status = 200

    def __init__(self, data, url, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
        self.data = BytesIO(data)
        self.url = url
        self.headers = Headers({"Content-Type": mime, "Content-Length": str(len(data))})

    def geturl(self):
        return self.url

    def read(self, amount=-1):
        return self.data.read(amount)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def make_xlsx(payload=b"sheet-data"):
    out = BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "<Types></Types>")
        z.writestr("xl/workbook.xml", "<workbook></workbook>")
        z.writestr("xl/worksheets/sheet1.xml", payload)
    blob = out.getvalue()
    # The service intentionally rejects implausibly tiny files.
    return blob + b"\0" * (max(0, 512 - len(blob)))


def sample_registry(*, url="https://www.cbr.ru/vfs/statistics/BankSector/Mortgage/a.xlsx"):
    return {"version": 1, "sources": [
        {"id": "one", "publisher": "Bank of Russia", "title": "Test workbook",
         "kind": "direct", "url": url, "enabled": True}
    ]}


class RegistryTests(unittest.TestCase):
    def test_fixed_registry_snapshot(self):
        sources = monitor.load_registry()
        self.assertEqual(len(sources), 44)
        self.assertEqual(len({s["id"] for s in sources}), 44)
        cbr = [s for s in sources if s["publisher"] == "Bank of Russia"]
        self.assertEqual(len(cbr), 41)
        canonical = "\n".join(s["id"] + " " + s["url"] for s in cbr)
        self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(), "c921a1ab1bc7bd6f0a5c2a097fa8be6810cf13b8fdf760da85ea5b1bc042d233")
        self.assertEqual([s["id"] for s in sources[-3:]],
                         ["minfin-fedbud-monthly", "minfin-fedbud-quarterly", "minfin-fedbud-annual"])

    def test_reject_unsupported_source_url(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "registry.json"
            d = sample_registry(url="https://127.0.0.1/private.xlsx")
            p.write_text(json.dumps(d), encoding="utf-8")
            with self.assertRaises(monitor.MonitorError):
                monitor.load_registry(p)

    def test_reject_duplicate_id(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "registry.json"
            d = sample_registry()
            d["sources"].append(d["sources"][0].copy())
            p.write_text(json.dumps(d), encoding="utf-8")
            with self.assertRaises(monitor.MonitorError):
                monitor.load_registry(p)


class SourceTests(unittest.TestCase):
    page = "https://minfin.gov.ru/ru/statistics/fedbud/execute/"

    def item(self, suffix):
        return {"page_url": self.page, "publisher": "Ministry of Finance of Russia",
                "file_stem": "Prilozhenie_3_dannye_109-111_", "file_suffix": suffix}

    def sample_html(self, *, prefix="2026/09"):
        return ("<html><a href='/common/upload/library/" + prefix +
                "/main/Prilozhenie_3_dannye_109-111_—_mes.xlsx'>Monthly</a>" +
                "<a href='/common/upload/library/" + prefix +
                "/main/Prilozhenie_3_dannye_109-111_%E2%80%94_kvartal.xlsx'>Quarterly</a>" +
                "<a href='/common/upload/library/" + prefix +
                "/main/Prilozhenie_3_dannye_109-111_—_god.xlsx'>Annual</a></html>")

    def test_minfin_three_attachments_and_page_cache(self):
        with patch.object(monitor, "open_source", return_value=Response(
                self.sample_html().encode(), self.page, "text/html")) as mocked:
            cache = {}
            links = [monitor.resolve_attachment(self.item(t), cache)
                     for t in ("_mes.xlsx", "_kvartal.xlsx", "_god.xlsx")]
            self.assertEqual(mocked.call_count, 1)
            self.assertTrue(all(link.startswith("https://minfin.gov.ru/common/upload/") for link in links))
            self.assertTrue(all("%E2%80%94" in link for link in links))

    def test_month_path_changes_without_registry_changes(self):
        with patch.object(monitor, "open_source", return_value=Response(
                self.sample_html(prefix="2026/11").encode(), self.page, "text/html")):
            url = monitor.resolve_attachment(self.item("_mes.xlsx"), {})
            self.assertIn("/2026/11/main/", url)

    def test_minfin_ambiguous_fails_closed(self):
        html = self.sample_html() + self.sample_html(prefix="2026/11")
        with patch.object(monitor, "open_source", return_value=Response(
                html.encode(), self.page, "text/html")):
            with self.assertRaisesRegex(monitor.MonitorError, "ATTACHMENT_AMBIGUOUS"):
                monitor.resolve_attachment(self.item("_mes.xlsx"), {})

    def test_minfin_external_link_rejected(self):
        html = '<a href="https://evil.example/common/upload/library/2026/09/main/Prilozhenie_3_dannye_109-111_—_mes.xlsx">bad</a>'
        with patch.object(monitor, "open_source", return_value=Response(
                html.encode(), self.page, "text/html")):
            with self.assertRaisesRegex(monitor.MonitorError, "URL_UNAPPROVED"):
                monitor.resolve_attachment(self.item("_mes.xlsx"), {})

    def test_minfin_missing_link_fails_closed(self):
        with patch.object(monitor, "open_source", return_value=Response(
                b'<a href="/dummy">n/a</a>', self.page, "text/html")):
            with self.assertRaisesRegex(monitor.MonitorError, "ATTACHMENT_NOT_FOUND"):
                monitor.resolve_attachment(self.item("_mes.xlsx"), {})

    def test_xlsx_validation(self):
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / "sample.xlsx"
            file.write_bytes(make_xlsx())
            monitor.verify_xlsx(file)
            file.write_bytes(b"<html>bad</html>")
            with self.assertRaises(monitor.MonitorError):
                monitor.verify_xlsx(file)

    def test_download_html_200_is_not_xlsx(self):
        url = sample_registry()["sources"][0]["url"]
        with patch.object(monitor, "open_source", return_value=Response(
                b"<html>Challenge</html>", url, "text/html")):
            with self.assertRaisesRegex(monitor.MonitorError, "SOURCE_NOT_XLSX"):
                monitor.download_hash(url, "Bank of Russia")

    def test_cbr_www_fallback_only_for_http_403(self):
        original = "https://cbr.ru/vfs/statistics/households/households_bm.xlsx"
        alternate = original.replace("https://cbr.ru/", "https://www.cbr.ru/")
        result = ("a" * 64, alternate, 1234)
        with patch.object(monitor, "_download_hash_single",
                          side_effect=[monitor.MonitorError("SOURCE_HTTP_403"), result]) as fetch:
            self.assertEqual(monitor.download_hash(original, "Bank of Russia"), result)
            self.assertEqual([call.args[0] for call in fetch.call_args_list],
                             [original, alternate])

    def test_no_cbr_fallback_on_other_failure_or_host(self):
        original = "https://cbr.ru/vfs/statistics/households/households_bm.xlsx"
        with patch.object(monitor, "_download_hash_single",
                          side_effect=monitor.MonitorError("SOURCE_HTTP_404")) as fetch:
            with self.assertRaisesRegex(monitor.MonitorError, "SOURCE_HTTP_404"):
                monitor.download_hash(original, "Bank of Russia")
            fetch.assert_called_once()
        with patch.object(monitor, "_download_hash_single",
                          side_effect=monitor.MonitorError("SOURCE_HTTP_403")) as fetch:
            with self.assertRaisesRegex(monitor.MonitorError, "SOURCE_HTTP_403"):
                monitor.download_hash(original.replace("https://cbr.ru/", "https://www.cbr.ru/"),
                                      "Bank of Russia")
            fetch.assert_called_once()

    def test_hashes_exact_download_bytes(self):
        url = sample_registry()["sources"][0]["url"]
        data = make_xlsx()
        with patch.object(monitor, "open_source", return_value=Response(data, url)):
            digest, final, size = monitor.download_hash(url, "Bank of Russia")
            self.assertEqual(digest, hashlib.sha256(data).hexdigest())
            self.assertEqual(size, len(data))
            self.assertEqual(final, url)


class StateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.registry = Path(self.tmp.name) / "registry.json"
        self.state = Path(self.tmp.name) / "state.json"
        self.registry.write_text(json.dumps(sample_registry()), encoding="utf-8")
        self.state.write_text(json.dumps({"version": 1, "items": {}}), encoding="utf-8")
        self.url = sample_registry()["sources"][0]["url"]
        self.first = "a" * 64
        self.second = "b" * 64

    def scan(self, *, hash_value=None, fail=False, token=None, chat_id=None, mode="check", dry=False):
        result = (hash_value or self.first, self.url, 12345)
        if fail:
            result = monitor.MonitorError("SOURCE_HTTP_503")
        with patch.object(monitor, "download_hash", side_effect=result if fail else None,
                          return_value=None if fail else result):
            return monitor.run_scan(mode, registry=self.registry, state_path=self.state,
                                    token=token, chat_id=chat_id, dry_run=dry)

    def test_silent_initial_baseline_and_unchanged(self):
        self.assertEqual(self.scan(mode="bootstrap"), 0)
        self.assertEqual(monitor.load_state(self.state)["items"]["one"]["sha256"], self.first)
        before = self.state.read_bytes()
        with patch.object(monitor, "send_telegram") as sender:
            self.assertEqual(self.scan(token="secret", chat_id="-123"), 0)
            sender.assert_not_called()
        self.assertEqual(self.state.read_bytes(), before)

    def test_changed_delivered_updates_state(self):
        self.scan(mode="bootstrap")
        with patch.object(monitor, "send_telegram") as sender:
            self.assertEqual(self.scan(hash_value=self.second, token="secret", chat_id="-123"), 0)
            sender.assert_called_once()
        self.assertEqual(monitor.load_state(self.state)["items"]["one"]["sha256"], self.second)

    def test_telegram_failure_preserves_previous_state(self):
        self.scan(mode="bootstrap")
        with patch.object(monitor, "send_telegram", side_effect=monitor.MonitorError("TELEGRAM_REJECTED")):
            self.assertEqual(self.scan(hash_value=self.second, token="secret", chat_id="-123"), 1)
        self.assertEqual(monitor.load_state(self.state)["items"]["one"]["sha256"], self.first)

    def test_download_failure_preserves_hash(self):
        self.scan(mode="bootstrap")
        self.assertEqual(self.scan(fail=True, token="secret", chat_id="-123"), 1)
        self.assertEqual(monitor.load_state(self.state)["items"]["one"]["sha256"], self.first)

    def test_dry_run_does_not_modify_state(self):
        self.scan(mode="bootstrap")
        before = self.state.read_bytes()
        with patch.object(monitor, "send_telegram") as sender:
            self.assertEqual(self.scan(hash_value=self.second, dry=True), 0)
            sender.assert_not_called()
        self.assertEqual(self.state.read_bytes(), before)

    def test_changed_url_same_sha_not_alerted(self):
        self.scan(mode="bootstrap")
        other = self.url.replace("/Mortgage/", "/mortgage/")
        with patch.object(monitor, "download_hash", return_value=(self.first, other, 12345)):
            with patch.object(monitor, "send_telegram") as sender:
                self.assertEqual(monitor.run_scan("check", registry=self.registry,
                    state_path=self.state, token="x", chat_id="-123"), 0)
                sender.assert_not_called()

    def test_missing_secrets_prevents_change(self):
        self.assertRaisesRegex(monitor.MonitorError, "TELEGRAM_NOT_CONFIGURED",
                               self.scan)
        self.assertEqual(monitor.load_state(self.state)["items"], {})


if __name__ == "__main__":
    unittest.main()
