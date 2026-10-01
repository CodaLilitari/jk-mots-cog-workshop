"""Optional reporter tests. Synthetic claims; no messages or external traffic."""
import contextlib
import copy
from email import policy
from email.parser import BytesParser
import io
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest import mock
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import reporting as r
from tools import workshop as w


def complete_report(kind="addition"):
    return {
        "schema_version": 1, "kind": kind, "title": "Synthetic test observation",
        "target": {"game": "jk", "version": "JK 1.01; synthetic test only", "base_game": "jk"},
        "research_review": {"release": "0.1.0", "references": ["docs/COG_WRITING_GUIDE.md: fixture reference"], "searches": ["Compared fixture term with the current notes; synthetic test only."], "comparison": "This fixture demonstrates report completeness; it is not a discovery."},
        "finding": {"claim": "Synthetic report claim.", "expected": "Fixture expectation.", "observed": "Fixture observation.", "reproduction": ["Construct a synthetic fixture.", "Inspect the documented output."], "evidence": "Unit test only; no retail executable ran.", "limitations": "No game execution or genuine novelty established.", "proposed_change": "No research change; this is a test fixture."},
        "credit": "Anonymous test fixture", "public_sources": [], "sharing_review": "Only synthetic information is included; no private material or attachments.",
    }


class ReporterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.env = mock.patch.dict(os.environ, {"COG_WORKSHOP_HOME": str(self.base / "managed"), "CODEX_HOME": str(self.base / "codex")})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.input = self.base / "finding.json"

    def write(self, value):
        self.input.write_text(json.dumps(value), encoding="utf-8")
        return self.input

    def test_template_is_incomplete(self):
        with self.assertRaises(r.ReportError):
            r.validate(r.template())

    def test_addition_and_correction_complete(self):
        for kind in ("addition", "correction"):
            with self.subTest(kind=kind):
                result, digest = r.render(complete_report(kind))
                self.assertEqual(result["to"], "lilitarikiralv@gmail.com")
                self.assertEqual(result["attachments"], [])
                self.assertIn(kind, result["subject"])
                self.assertIn("novelty, correctness and acceptance require independent review", result["body"])
                self.assertEqual(len(digest), 64)

    def test_required_comparison_and_evidence_fields(self):
        for group, names in (("research_review", ("release", "references", "searches", "comparison")), ("finding", ("claim", "expected", "observed", "reproduction", "evidence", "limitations", "proposed_change"))):
            for name in names:
                report = complete_report("correction")
                report[group][name] = [] if isinstance(report[group][name], list) else ""
                with self.subTest(group=group, name=name), self.assertRaises(r.ReportError):
                    r.validate(report)

    def test_target_exactness_and_base_game(self):
        for target in ({"game": "enhanced", "version": "OpenJKDF2 fixture commit abc", "base_game": "mots"}, {"game": "mots", "version": "Original MotS fixture", "base_game": "mots"}):
            report = complete_report()
            report["target"] = target
            self.assertEqual(r.validate(report)["target"], target)
        for target in ({"game": "jk", "version": "1.01", "base_game": "mots"}, {"game": "enhanced", "version": "", "base_game": "jk"}, {"game": "unknown", "version": "x", "base_game": "jk"}):
            report = complete_report()
            report["target"] = target
            with self.assertRaises(r.ReportError):
                r.validate(report)

    def test_no_attachment_or_recipient_override(self):
        for name, value in (("attachments", ["private.cog"]), ("to", "someone@example.invalid"), ("send", True)):
            report = complete_report()
            report[name] = value
            with self.assertRaises(r.ReportError):
                r.validate(report)

    def test_header_injection_and_length_guards(self):
        for title in ("x\r\nBcc: other@example.invalid", "x\nCc: other@example.invalid", "x\tvalue", "x\x00value", "x" * 161):
            report = complete_report()
            report["title"] = title
            with self.assertRaises(r.ReportError):
                r.render(report)
        self.input.write_bytes(b"x" * (r.MAX_REPORT_BYTES + 1))
        with self.assertRaises(r.ReportError):
            r.load_report(self.input)

    def test_duplicate_json_fields_rejected(self):
        self.input.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
        with self.assertRaises(r.ReportError):
            r.load_report(self.input)

    def test_exact_email_preview_and_content_hash(self):
        receipt = r.prepare(self.write(complete_report()), self.base / "review")
        message = BytesParser(policy=policy.default).parsebytes((self.base / "review.eml").read_bytes())
        self.assertEqual(message["To"], r.RECIPIENT)
        self.assertEqual(message["Subject"], receipt["subject"])
        self.assertIsNone(message["From"])
        self.assertIsNone(message["Bcc"])
        self.assertEqual(list(message.iter_attachments()), [])
        self.assertEqual(message.get_content().replace("\r\n", "\n"), receipt["body"])
        self.assertEqual((self.base / "review.md").read_text(encoding="utf-8"), receipt["body"])
        self.assertEqual(receipt["status"], "prepared_not_sent")
        self.assertEqual(receipt["novelty_status"], "contributor_proposal_not_independently_verified")
        self.assertEqual(json.loads((self.base / "review.review.json").read_text(encoding="utf-8")), receipt)
        changed = complete_report()
        changed["finding"]["observed"] += " Changed."
        self.assertNotEqual(r.render(changed)[1], receipt["report_sha256"])

    def test_existing_outputs_never_overwritten(self):
        marker = self.base / "review.eml"
        marker.write_text("preserve", encoding="utf-8")
        with self.assertRaises(r.ReportError):
            r.prepare(self.write(complete_report()), self.base / "review")
        self.assertEqual(marker.read_text(), "preserve")
        self.assertFalse((self.base / "review.md").exists())

    def test_partial_write_failure_cleans_only_new_outputs(self):
        self.write(complete_report())
        original = Path.open
        def failing_open(path, *args, **kwargs):
            if path.name == "review.eml":
                raise OSError("synthetic write failure")
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "open", failing_open), self.assertRaises(OSError):
            r.prepare(self.input, self.base / "review")
        self.assertFalse((self.base / "review.md").exists())
        self.assertTrue(self.input.exists())

    def test_cli_reporting_never_updates_connects_or_launches_client(self):
        with mock.patch.object(w, "update", side_effect=AssertionError("No update allowed")) as update, mock.patch.object(socket.socket, "connect", side_effect=AssertionError("No network allowed")) as connect, mock.patch.object(w.subprocess, "call", side_effect=AssertionError("No child/client allowed")) as child, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(w.main(["report", "template", "--out", str(self.base / "template.json")]), 0)
            self.write(complete_report())
            self.assertEqual(w.main(["report", "prepare", str(self.input), "--out-prefix", str(self.base / "prepared")]), 0)
            update.assert_not_called()
            connect.assert_not_called()
            child.assert_not_called()
        self.assertFalse((self.base / "managed").exists())

    def test_unknown_and_wrong_type_schema_rejected(self):
        for report in ([], None, "x", {"schema_version": True}, {**complete_report(), "unexpected": "x"}):
            with self.subTest(report_type=type(report).__name__), self.assertRaises(r.ReportError):
                r.validate(report)


if __name__ == "__main__":
    unittest.main()
