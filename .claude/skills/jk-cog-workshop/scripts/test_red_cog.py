"""Tests for Red's fork additions: optional catalog, capacity and finding smoke checks. Standard library only."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(script: str, *args: str) -> tuple[int, str, str]:
    done = subprocess.run([sys.executable, "-B", str(HERE / script), *args], capture_output=True, text=True)
    return done.returncode, done.stdout, done.stderr


class OptionalCatalog(unittest.TestCase):
    def test_bundled_stats_and_notes_without_catalog(self) -> None:
        code, out, _ = run("corpus.py", "stats")
        self.assertEqual(code, 0)
        stats = json.loads(out)
        self.assertEqual(stats["catalog"], "not bundled")
        self.assertIn("public_export", stats)
        code, out, _ = run("corpus.py", "search", "SendTrigger", "--limit", "2")
        self.assertEqual(code, 0)
        rows = [json.loads(line) for line in out.splitlines()]
        self.assertEqual(rows[0]["kind"], "hint")
        self.assertTrue(all(r["kind"] == "note" for r in rows[1:]))
        self.assertGreaterEqual(len(rows), 2)
        code, _, err = run("corpus.py", "show", "deadbeef")
        self.assertNotEqual(code, 0)
        self.assertIn("No corpus catalog", err)

    def test_search_and_show_with_a_catalog_root(self) -> None:
        body = b"symbols\nmessage startup\nend\ncode\nstartup:\nreturn;\nend\n"
        digest = hashlib.sha256(body).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "catalog").mkdir()
            row = {"sha256": digest, "bytes": len(body), "names": ["cog/probe.cog"], "games": ["jk"],
                   "calls": {}, "messages": ["startup"], "tags": ["synthetic"], "provenance": []}
            (root / "catalog" / "cogs.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
            (root / "catalog" / "sources.jsonl").write_text("", encoding="utf-8")
            code, out, _ = run("corpus.py", "--root", str(root), "search", "probe.cog", "--kind", "cog")
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out.splitlines()[0])["sha256"], digest)
            code, out, _ = run("corpus.py", "--root", str(root), "show", digest)
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)["names"], ["cog/probe.cog"])


class Smoke(unittest.TestCase):
    def test_static_capacity_fits_and_shortfall(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            items = root / "items.dat"
            items.write_text("item 1 0 1 0x120 cog=power.cog\nend\n", encoding="utf-8")
            roomy, tight = root / "roomy.jkl", root / "tight.jkl"
            roomy.write_text("SECTION: COGS\nWorld cogs 20\n0: startup.cog\nend\n", encoding="utf-8")
            tight.write_text("SECTION: COGS\nWorld cogs 5\n0: startup.cog\nend\n", encoding="utf-8")
            code, out, _ = run("audit_static_capacity.py", str(roomy), str(items), "--reserve", "8")
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)["instance_budget"]["headroom"], 10)
            code, out, _ = run("audit_static_capacity.py", str(tight), str(items), "--reserve", "8")
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(out)["instance_budget"]["shortfall"], 5)

    def test_finding_template_is_never_sent_and_incomplete_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            template = Path(tmp) / "finding.json"
            code, out, _ = run("prepare_finding.py", "template", "--out", str(template))
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)["status"], "template_only_not_sent")
            code, out, _ = run("prepare_finding.py", "prepare", str(template), "--out-prefix", str(Path(tmp) / "draft"))
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(out)["status"], "not_sent")


if __name__ == "__main__":
    unittest.main()
