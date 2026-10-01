"""Isolated installed-skill launch and registration tests; no network or user install."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import workshop as w

WRAPPER = w.ROOT / "skill/jk-mots-cog-workflow/scripts/workshop.py"
SPEC = importlib.util.spec_from_file_location("skill_launcher", WRAPPER)
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


class SkillLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.home = self.base / "nondefault-managed-home"
        self.source = self.base / "extracted"
        self.target = self.base / "skills/public"
        self.make_tree(self.source, "0.0.1")
        w.install_skill(self.home, self.source, self.target)

    def tearDown(self):
        self.temp.cleanup()

    def make_tree(self, root, version):
        (root / "tools").mkdir(parents=True)
        scripts = root / "skill/jk-mots-cog-workflow/scripts"
        scripts.mkdir(parents=True)
        for name in ("cog_workshop.py", "tools/workshop.py", "tools/reporting.py", "tools/__init__.py"):
            shutil.copyfile(w.ROOT / name, root / name)
        shutil.copyfile(WRAPPER, scripts / "workshop.py")
        (scripts.parent / "SKILL.md").write_text("fixture " + version, encoding="utf-8")
        w.atomic_json(root / "release.json", {"schema_version": 1, "product": w.PRODUCT, "version": version})

    def run_wrapper(self, *args, env=None):
        return subprocess.run([sys.executable, "-B", str(self.target / "scripts/workshop.py"), *args],
                              capture_output=True, text=True, env=env)

    def test_custom_home_and_launcher_are_registered_only_locally(self):
        registered, home = launcher.registered_launcher(self.target)
        self.assertEqual(registered, self.source / "cog_workshop.py")
        self.assertEqual(home, self.home)
        self.assertFalse((self.source / "skill/jk-mots-cog-workflow/.workshop-install.json").exists())
        receipt = w.read_json(self.home / "skill-install.json")
        self.assertEqual(receipt["files"], w.tree_hashes(self.target))

    def test_real_offline_wrapper_uses_custom_home_without_check(self):
        result = self.run_wrapper("--offline", "version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "0.0.1")
        self.assertFalse((self.home / "check-state.json").exists())

    def test_real_opt_out_controls_do_not_check(self):
        for args, extra in ((("--no-auto-update", "version"), {}), (("version",), {"COG_WORKSHOP_AUTO_UPDATE": "0"}), (("version",), {"COG_WORKSHOP_OFFLINE": "1"})):
            with self.subTest(args=args, extra=extra):
                result = self.run_wrapper(*args, env={**os.environ, **extra})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse((self.home / "check-state.json").exists())

    def test_normal_entry_point_delegates_daily_check_and_never_duplicates_logic(self):
        def dispatch(command):
            self.assertEqual(command[:3], [sys.executable, "-B", str(self.source / "cog_workshop.py")])
            with mock.patch.object(w, "ROOT", self.source):
                return w.main(command[3:])
        with mock.patch.object(launcher, "SKILL_ROOT", self.target), mock.patch.object(launcher.subprocess, "call", side_effect=dispatch), mock.patch.object(w, "update", return_value={"status": "current"}) as update, mock.patch.dict(os.environ, {"COG_WORKSHOP_OFFLINE": "0", "COG_WORKSHOP_AUTO_UPDATE": "1"}), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(launcher.main([]), 0)
            update.assert_called_once_with(self.home, w.DEFAULT_FEED, source_root=self.source)
            update.reset_mock()
            w.atomic_json(self.home / "check-state.json", {"checked_at": int(time.time())})
            self.assertEqual(launcher.main(["version"]), 0)
            update.assert_not_called()

    def test_real_report_draft_bypasses_update_without_offline_flag(self):
        output = self.base / "finding.json"
        result = self.run_wrapper("report", "template", "--out", str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "template_only_not_sent")
        self.assertTrue(output.is_file())
        self.assertFalse((self.home / "check-state.json").exists())

    def test_sync_repoints_wrapper_to_new_release_and_preserves_private_skill(self):
        private = self.base / "skills/jk-mots-cog-workflow"
        private.mkdir()
        (private / "private.cog").write_text("private evidence")
        newer = self.base / "new-release"
        self.make_tree(newer, "0.2.0")
        self.assertEqual(w.sync_installed_skill(self.home, newer)["status"], "installed")
        self.assertEqual(launcher.registered_launcher(self.target)[0], newer / "cog_workshop.py")
        result = self.run_wrapper("--offline", "version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "0.2.0")
        self.assertEqual((private / "private.cog").read_text(), "private evidence")

    def test_moved_launcher_fails_closed_and_can_reconnect_unchanged_skill(self):
        moved = self.base / "moved-extraction"
        shutil.move(str(self.source), moved)
        result = self.run_wrapper("version")
        self.assertEqual(result.returncode, 1)
        self.assertIn("moved or is missing", result.stderr)
        self.assertFalse((self.home / "check-state.json").exists())
        w.install_skill(self.home, moved, self.target)
        result = self.run_wrapper("--offline", "version")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_copied_skill_and_invalid_metadata_never_dispatch(self):
        other = self.base / "copied-skill"
        shutil.copytree(self.target, other)
        for root in (other, self.base / "unregistered"):
            with mock.patch.object(launcher, "SKILL_ROOT", root), mock.patch.object(launcher.subprocess, "call") as child, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(launcher.main(["version"]), 1)
                child.assert_not_called()
        w.atomic_json(self.home / "skill-install.json", {"target": str(self.target), "launcher": "relative.py"})
        with mock.patch.object(launcher, "SKILL_ROOT", self.target), mock.patch.object(launcher.subprocess, "call") as child, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(launcher.main(["version"]), 1)
            child.assert_not_called()


if __name__ == "__main__":
    unittest.main()
