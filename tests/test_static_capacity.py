"""Synthetic authored-input accounting tests; no game or external traffic."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skill/jk-mots-cog-workflow/scripts/audit_static_capacity.py"
spec = importlib.util.spec_from_file_location("audit_static_capacity", SCRIPT)
capacity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capacity)
sys.path.insert(0, str(ROOT))
from tools import workshop


def static(count=5, rows="0: startup.cog\n"):
    return "SECTION: COGS\nWorld cogs " + str(count) + "\n" + rows + "end\n"


def items(rows="item 1 0 1 0x120 cog=power.cog\n"):
    return rows + "end\n"


class StaticCapacityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.jkl = self.root / "static.jkl"
        self.dat = self.root / "items.dat"
        self.write()

    def write(self, jkl=None, dat=None):
        self.jkl.write_bytes((static() if jkl is None else jkl).encode("ascii"))
        self.dat.write_bytes((items() if dat is None else dat).encode("ascii"))

    def audit(self, reserve=0):
        return capacity.audit(self.jkl, self.dat, reserve)

    def test_enough_capacity_and_exact_input_hashes(self):
        result = self.audit()
        self.assertEqual(result["status"], "fits")
        self.assertEqual(result["instance_budget"]["headroom"], 3)
        self.assertEqual(result["instance_budget"]["required_instances"], 2)
        for label, path in (("static_jkl", self.jkl), ("items_dat", self.dat)):
            self.assertEqual(result["inputs"][label]["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(result["script_table"]["status"], "not_assessed")
        self.assertIn("SM Sith Lord", result["credit"]["inspiration"])

    def test_shortage_and_explicit_reserve(self):
        result = self.audit(4)
        self.assertEqual(result["status"], "shortfall")
        self.assertEqual(result["instance_budget"]["headroom"], -1)
        self.assertEqual(result["instance_budget"]["shortfall"], 1)
        self.assertEqual(result["instance_budget"]["reserved_instances"], 4)
        self.assertEqual(self.audit(3)["instance_budget"]["headroom"], 0)

    def test_every_binding_counts_even_same_row_same_file_or_same_bin(self):
        self.write(static(6, "0: repeated.cog\n1: repeated.cog\n"),
                   items("one 1 0 1 1 cog=repeated.cog cog=repeated.cog\ntwo 1 0 1 1 cog=repeated.cog\n"))
        budget = self.audit()["instance_budget"]
        self.assertEqual(budget["placed_instances"], 2)
        self.assertEqual(budget["item_instances"], 3)
        self.assertEqual(budget["headroom"], 1)

    def test_p68_shaped_shortfall_is_synthetic_not_recovered_content(self):
        self.write(static(35, ""), items("".join(f"item{i} {i} 0 1 1 cog=fixture.cog\n" for i in range(40))))
        self.assertEqual(self.audit()["instance_budget"]["shortfall"], 5)

    def test_case_commas_backslash_and_supported_comments(self):
        self.write("; comment\nSECTION: COGS\nWORLD COGS 5 # cap\n0: Folder\\Shared.COG\nEND\n",
                   "# comment\n  # indented hash\nITEM,1,0,1,0X120,COG=Folder\\Shared.COG # note\nEND\n")
        result = self.audit()
        self.assertEqual(result["status"], "fits")
        self.assertEqual(result["observations"]["items_dat"]["bindings"][0]["script"], "Folder\\Shared.COG")

    def test_semicolon_is_not_an_inline_or_indented_comment(self):
        for text in (items(" ; not-column-zero\n"), items("item 1 0 1 1 ; extra\n")):
            self.write(dat=text)
            self.assertEqual(self.audit()["status"], "unknown")

    def test_script_table_is_not_substituted_for_instance_capacity(self):
        self.write("SECTION: COGSCRIPTS\nWorld scripts 200\n0: shared.cog\nend\n" + static(1), items())
        result = self.audit()
        self.assertEqual(result["status"], "shortfall")
        self.assertEqual(result["instance_budget"]["capacity"], 1)
        self.assertEqual(result["script_table"]["status"], "not_assessed")

    def test_zero_capacity_with_and_without_consumers(self):
        self.write(static(0, ""), items(""))
        self.assertEqual(self.audit()["instance_budget"]["headroom"], 0)
        self.assertEqual(self.audit()["status"], "fits")
        self.write(static(0, ""), items())
        self.assertEqual(self.audit()["status"], "shortfall")

    def test_missing_duplicate_malformed_headers_and_end_are_unknown(self):
        cases = ["", "World cogs 1\nend\n", "SECTION: COGS\nend\n",
                 "SECTION: COGS\nWorld cogs 5\n", static() + static(),
                 static().replace("World cogs 5", "World cogs 5\nWorld cogs 5"),
                 static().replace("World cogs 5", "World cogs -1"),
                 static().replace("World cogs 5", "World cogs 5 extra"),
                 static().replace("end", "SECTION: SOUNDS\nend"),
                 static().replace("end", "end extra"), static() + "end\n",
                 static(5, "bad-row\n"), static(5, "0: a.cog\n0: b.cog\n")]
        for text in cases:
            with self.subTest(text=text):
                self.write(jkl=text)
                result = self.audit()
                self.assertEqual(result["status"], "unknown")
                self.assertIsNone(result["instance_budget"])

    def test_malformed_items_and_unterminated_input_are_unknown(self):
        cases = ["", "item 1 0 1 1 cog=a.cog\n", "end\nend\n", "end extra\n",
                 items("item 1 0 1\n"), items("item -1 0 1 1\n"),
                 items("item 200 0 1 1\n"), items("item 1x 0 1 1\n"),
                 items("item 1 nan 1 1\n"), items("item 1 0 1e999 1\n"),
                 items("item 1 0 1 invalid\n"), items("item 1 0 1 1 cog=\n"),
                 items("item 1 0 1 1 cog = a.cog\n"), items("item 1 0 1 1 cog\n"),
                 items('item 1 0 1 1 cog="a.cog"\n'), items("item 1 0 1 1 cog=a.cog " + chr(92) + "\n"),
                 items("item 1 0 1 1 =value\n")]
        for text in cases:
            with self.subTest(text=text):
                self.write(dat=text)
                result = self.audit()
                self.assertEqual(result["status"], "unknown")
                self.assertIsNone(result["instance_budget"])

    def test_other_optional_fields_do_not_consume_cog_instances(self):
        self.write(dat=items("item 1 0 1 1 sound=test.wav cog=a.cog other=value\n"))
        self.assertEqual(self.audit()["instance_budget"]["item_instances"], 1)

    def test_unsupported_line_separators_and_control_bytes_fail_closed(self):
        for separator in ("\x0b", "\x0c", "\x85", "\r"):
            with self.subTest(separator=repr(separator)):
                self.jkl.write_bytes(static().replace("\n", separator).encode("latin-1"))
                result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.jkl), str(self.dat)],
                                        capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(json.loads(result.stdout)["status"], "unknown")
        for control in ("\x00", "\x01", "\x0b", "\x7f", "\x85"):
            self.write()
            self.dat.write_bytes(("# comment " + control + "\n" + items()).encode("latin-1"))
            self.assertEqual(self.audit()["status"], "unknown")
        self.write(static().replace("\n", "\r\n"), items().replace("\n", "\r\n"))
        self.assertEqual(self.audit()["status"], "fits")

    def test_invalid_reserve_is_unknown(self):
        for value in (-1, True, 1.2, "2", 2147483648):
            with self.subTest(value=value):
                self.assertEqual(self.audit(value)["status"], "unknown")

    def test_read_limits_and_missing_input_fail_closed(self):
        with mock.patch.object(capacity, "MAX_BYTES", 8):
            self.assertEqual(self.audit()["status"], "unknown")
        self.write(dat=items("x" * 1024 + "\n"))
        self.assertEqual(self.audit()["status"], "unknown")
        self.dat.unlink()
        self.assertEqual(self.audit()["status"], "unknown")

    def test_deterministic_json_and_input_bytes_unchanged(self):
        before = (self.jkl.read_bytes(), self.dat.read_bytes())
        outputs = []
        for _ in range(2):
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                self.assertEqual(capacity.main([str(self.jkl), str(self.dat)]), 0)
            outputs.append(stream.getvalue())
        self.assertEqual(*outputs)
        self.assertEqual(before, (self.jkl.read_bytes(), self.dat.read_bytes()))

    def test_direct_cli_exit_statuses_and_json(self):
        for expected_status, expected_exit, jkl, dat in (
            ("fits", 0, static(), items()), ("shortfall", 1, static(1), items()),
            ("unknown", 2, static(), "incomplete")):
            self.write(jkl, dat)
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.jkl), str(self.dat)],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, expected_exit, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], expected_status)

    def test_workshop_cli_skips_updater_and_storage_even_without_offline(self):
        with mock.patch.object(workshop, "outside_checkout", side_effect=AssertionError("storage must not run")), mock.patch.object(workshop, "update", side_effect=AssertionError("update must not run")), mock.patch.object(workshop.subprocess, "call", return_value=1) as child:
            code = workshop.main(["capacity", str(self.jkl), str(self.dat), "--reserve", "4"])
            self.assertEqual(code, 1)
            self.assertIn("-B", child.call_args.args[0])
            self.assertEqual(child.call_args.args[0][-2:], ["--reserve", "4"])
        home = self.root / "must-not-be-created"
        result = subprocess.run([sys.executable, "-B", str(ROOT / "cog_workshop.py"), "--home", str(home),
                                 "capacity", str(self.jkl), str(self.dat), "--reserve", "4"],
                                capture_output=True, text=True, timeout=15,
                                env={**os.environ, "COG_WORKSHOP_AUTO_UPDATE": "1"})
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "shortfall")
        self.assertFalse(home.exists())


if __name__ == "__main__":
    unittest.main()
