"""Offline integrity, extraction and Git-effect tests for the CBR offices series."""
from __future__ import annotations

import contextlib
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import capture_cbr_offices as m

FIXTURES = Path(__file__).parent / "fixtures" / "cbr-offices"
BASIC = (FIXTURES / "basic.html").read_text(encoding="utf-8")
GROUPED = (FIXTURES / "grouped-header.html").read_text(encoding="utf-8")


def sample():
    rows, physical = m.extract_records(BASIC)
    return rows, physical, m.serialize_csv(rows)


def cmd(path, *args):
    return subprocess.run(["git", "-C", str(path), *args],
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()


@contextlib.contextmanager
def cwd(path):
    old = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


class ExtractionTests(unittest.TestCase):
    def test_seven_columns_and_nine_output_fields(self):
        records, physical, csv_bytes = sample()
        self.assertEqual((physical, len(records)), (2, 8))
        self.assertEqual(m.validate_csv_bytes(csv_bytes), (2, 8))
        self.assertEqual(records[0], ("3", "Центральный федеральный округ",
                                      "Белгородская область", 'АО "Россельхозбанк"',
                                      "3349", "4", "Головные офисы", "", "blank"))
        self.assertEqual(records[4][1], "-")
        self.assertEqual(records[4][4], "0007")
        self.assertEqual([x[-2] for x in records[4:8]], ["0", "—", "", "1"])
        self.assertIn(b'"', csv_bytes)
        self.assertEqual(csv_bytes, m.serialize_csv(m.extract_records(BASIC)[0]))

    def test_rowspan_hierarchical_header(self):
        records, physical = m.extract_records(GROUPED)
        self.assertEqual((physical, len(records)), (2, 4))
        self.assertEqual(records[0][6], "Подразделения / Филиалы")
        self.assertEqual(records[2][2], "Тестовый регион")
        self.assertEqual(m.validate_csv_bytes(m.serialize_csv(records)), (2, 4))

    def test_new_column_and_unknown_region(self):
        text = BASIC.replace("<th>Допофисы</th>", "<th>Иные подразделения</th><th>Допофисы</th>")
        text = text.replace('colspan="7"', 'colspan="8"')
        text = text.replace('<td>3349</td><td></td><td>1</td><td>18</td><td>19</td>',
                            '<td>3349</td><td></td><td>1</td><td>5</td><td>18</td><td>19</td>')
        text = text.replace('<td>0007</td><td>0</td><td>—</td><td></td><td>1</td>',
                            '<td>0007</td><td>0</td><td>—</td><td>6</td><td></td><td>1</td>')
        records, n = m.extract_records(text.replace("Новый регион", "Другой субъект"))
        self.assertEqual((n, len(records)), (2, 10))
        self.assertEqual(records[2][6], "Иные подразделения")
        self.assertEqual(records[5][2], "Другой субъект")

    def test_untrusted_formula_text_is_not_executed_or_modified(self):
        text = BASIC.replace("Банк &quot;Кот, и Ко&quot;", "=HYPERLINK(&quot;evil&quot;)")
        records, _ = m.extract_records(text)
        self.assertEqual(records[4][3], '=HYPERLINK("evil")')

    def test_invalid_html_fails_closed(self):
        variants = [
            BASIC.replace("Рег. № КО", "Иной идентификатор"),
            BASIC.replace('colspan="7"', 'colspan="6"'),
            BASIC.replace('colspan="7"', 'colspan="0"'),
            BASIC.replace("</tbody>", "<tr><td>Неизвестный итог</td></tr></tbody>"),
            BASIC.replace("(ОКЭР).", "(OTHER)."),
            BASIC.replace('Россельхозбанк', 'Bad\x1b[31m'),
            "<p>Not a source table</p>" + m.KNOWN_CONTEXT,
        ]
        for html in variants:
            with self.subTest(variant=html[:80]):
                with self.assertRaises(m.CaptureError):
                    m.extract_records(html)

    def test_duplicate_source_table_fails(self):
        first = BASIC.split('<table id="cstat">', 1)[1].split("</table>", 1)[0]
        duplicate = BASIC.replace("</body>", '<table id="cstat">' + first + "</table></body>")
        with self.assertRaisesRegex(m.CaptureError, "SOURCE_TABLE_AMBIGUOUS"):
            m.extract_records(duplicate)


class CsvAndBoundaryTests(unittest.TestCase):
    def test_malformed_csv_rejected(self):
        _, _, valid = sample()
        invalid = [valid.replace(b"\n", b"\r\n"),
                   valid.replace(b",blank\n", b",present\n", 1),
                   valid.replace(b"3349", b"", 1),
                   valid.replace(b",4,", b",5,", 1),
                   valid + b"junk\n"]
        for value in invalid:
            with self.assertRaises(m.CaptureError):
                m.validate_csv_bytes(value)

    def test_utc4_new_year_uses_capture_instant(self):
        self.assertEqual(m.filename_for(datetime(2026, 12, 31, 19, 59, tzinfo=timezone.utc)),
                         "OFFICES_2026-12-31.csv")
        self.assertEqual(m.filename_for(datetime(2026, 12, 31, 20, 0, tzinfo=timezone.utc)),
                         "OFFICES_2027-01-01.csv")
        with self.assertRaises(m.CaptureError):
            m.file_date("OFFICES_2027-02-30.csv")
        with self.assertRaises(m.CaptureError):
            m.file_date("../../bad.csv")

    def test_capture_outputs_only_csv_and_hash(self):
        _, _, data = sample()
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            output = directory / "output"
            output.mkdir()
            with patch.object(m, "fetch_source_html", return_value=(BASIC, datetime(2027, 1, 1, tzinfo=m.TZ))):
                target = m.capture(output, directory / "gh-output")
            self.assertEqual(target.name, "OFFICES_2027-01-01.csv")
            self.assertEqual(target.read_bytes(), data)
            self.assertEqual((directory / "gh-output").read_text(),
                             "csv_sha256=" + hashlib.sha256(data).hexdigest() + "\n")
            self.assertEqual(len(list(output.iterdir())), 1)

    def test_artifact_extra_symlink_and_corruption_rejected(self):
        _, _, data = sample()
        h = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            file = directory / "OFFICES_2026-11-09.csv"
            file.write_bytes(data)
            self.assertEqual(m.validate_artifact(directory, h)[1], data)
            with self.assertRaisesRegex(m.CaptureError, "ARTIFACT_HASH_MISMATCH"):
                m.validate_artifact(directory, "0" * 64)
            (directory / "extra").write_text("extra")
            with self.assertRaisesRegex(m.CaptureError, "ARTIFACT_FILE_COUNT"):
                m.validate_artifact(directory, h)
            (directory / "extra").unlink()
            file.unlink()
            file.symlink_to("/etc/hosts")
            with self.assertRaisesRegex(m.CaptureError, "ARTIFACT_FILE_TYPE"):
                m.validate_artifact(directory, h)

    def test_redirect_validation_never_allows_external_host(self):
        for u in ("http://www.cbr.ru/banking_sector/credit/cstat/",
                  "https://evil.test/banking_sector/credit/cstat/",
                  "https://127.0.0.1/banking_sector/credit/cstat/",
                  "https://www.cbr.ru@evil.test/banking_sector/credit/cstat/"):
            with self.assertRaisesRegex(m.CaptureError, "SOURCE_REDIRECT_REJECTED"):
                m.validate_url(u)
        m.validate_url(m.SOURCE_URL)

    def test_http_bad_mime_and_length(self):
        from email.message import Message
        class Response:
            status = 200
            def __init__(self, mime, length=None):
                self.headers = Message()
                self.headers["Content-Type"] = mime
                if length:
                    self.headers["Content-Length"] = length
            def __enter__(self): return self
            def __exit__(self, *x): return False
            def geturl(self): return m.SOURCE_URL
            def read(self, n): return b"html"[:n]
        for response, error in ((Response("application/json"), "SOURCE_MIME_INVALID"),
                                (Response("text/html", str(m.MAX_HTML + 1)), "SOURCE_SIZE_LIMIT"),
                                (Response("text/html", "9"), "SOURCE_TRUNCATED")):
            class Opener:
                def open(self, *args, **kwargs): return response
            with patch.object(m.urllib.request, "build_opener", return_value=Opener()):
                with self.assertRaisesRegex(m.CaptureError, error):
                    m.fetch_source_html()


class GitEffectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.bare, self.work = root / "remote.git", root / "checkout"
        subprocess.run(["git", "init", "--bare", "--initial-branch=main", str(self.bare)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "clone", str(self.bare), str(self.work)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cmd(self.work, "config", "user.name", "test")
        cmd(self.work, "config", "user.email", "test@example.com")
        (self.work / "README.md").write_text("baseline")
        cmd(self.work, "add", "README.md")
        cmd(self.work, "commit", "-m", "baseline")
        cmd(self.work, "push", "origin", "HEAD:refs/heads/main")
        self.initial = cmd(self.work, "rev-parse", "HEAD")
        self.data = sample()[2]

    def publish(self, iso="2026-11-09", data=None, sha=None):
        with cwd(self.work):
            return m.publish_immutably("OFFICES_" + iso + ".csv",
                                         self.data if data is None else data,
                                         self.initial if sha is None else sha,
                                         self.work, strict_remote=False)

    def test_only_one_added_file_and_new_year(self):
        self.assertEqual(self.publish("2027-01-01"), "CREATED")
        relative = m.CORPUS_ROOT + "/2027/OFFICES_2027-01-01.csv"
        head = cmd(self.bare, "rev-parse", "refs/heads/main")
        self.assertEqual(cmd(self.bare, "diff-tree", "--no-commit-id", "--name-status", "-r", head),
                         "A\t" + relative)
        self.assertEqual((self.work / relative).read_bytes(), self.data)

    def test_same_day_idempotent_or_conflict(self):
        self.assertEqual(self.publish(), "CREATED")
        published = cmd(self.bare, "rev-parse", "refs/heads/main")
        cmd(self.work, "reset", "--hard", self.initial)
        self.assertEqual(self.publish(), "NOOP_ALREADY_PUBLISHED")
        with self.assertRaisesRegex(m.CaptureError, "SAME_DAY_CONFLICT"):
            self.publish(data=self.data.replace(b"3349", b"1234"))
        self.assertEqual(cmd(self.bare, "rev-parse", "refs/heads/main"), published)

    def test_remote_policy_generation_change_blocks_stale_publisher(self):
        (self.work / "another.txt").write_text("concurrent")
        cmd(self.work, "add", "another.txt")
        cmd(self.work, "commit", "-m", "concurrent")
        cmd(self.work, "push", "origin", "HEAD:refs/heads/main")
        cmd(self.work, "reset", "--hard", self.initial)
        with self.assertRaisesRegex(m.CaptureError, "POLICY_GENERATION_CHANGED"):
            self.publish()

    def test_checkout_sha_dirty_tree_and_wrong_root_rejected(self):
        with self.assertRaisesRegex(m.CaptureError, "PUBLISH_CODE_COMMIT_MISMATCH"):
            self.publish(sha="0" * 40)
        (self.work / "untracked").write_text("untrusted")
        with self.assertRaisesRegex(m.CaptureError, "PUBLISH_WORKTREE_DIRTY"):
            self.publish()
        (self.work / "untracked").unlink()
        with cwd(self.work):
            with self.assertRaisesRegex(m.CaptureError, "PUBLISH_ROOT_INVALID"):
                m.publish_immutably("OFFICES_2026-11-09.csv", self.data,
                                    self.initial, self.work, "../../x", strict_remote=False)


if __name__ == "__main__":
    unittest.main()
