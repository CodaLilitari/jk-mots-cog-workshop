"""Offline fault, security and real child-process upgrade tests."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import workshop as w


class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.home = self.base / "managed"
        self.source = self.base / "source"
        self.make_tree(self.source, "0.0.1")
        self.zip, self.latest = self.make_package("0.2.0")

    def tearDown(self):
        self.temp.cleanup()

    def make_tree(self, root, version):
        (root / "tools").mkdir(parents=True)
        (root / "skill/jk-mots-cog-workflow").mkdir(parents=True)
        w.atomic_json(root / "release.json", {"schema_version": 1, "product": w.PRODUCT, "version": version})
        (root / "skill/jk-mots-cog-workflow/SKILL.md").write_text("---\nname: jk-mots-cog-workflow-public\ndescription: Fixture.\n---\n" + version, encoding="utf-8")
        for name in ("cog_workshop.py", "tools/workshop.py", "tools/reporting.py", "tools/__init__.py"):
            shutil.copyfile(w.ROOT / name, root / name)

    def make_package(self, version):
        tree = self.base / ("tree-" + version)
        self.make_tree(tree, version)
        package = self.base / (version + ".zip")
        with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in tree.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(tree).as_posix())
        latest = {"version": version, "url": "https://portfolio.example/downloads/release.zip", "size": package.stat().st_size, "sha256": w.sha256_file(package), "mirrors": []}
        return package, latest

    def activate(self, package=None, latest=None):
        return w.activate_package(package or self.zip, latest or self.latest, self.home, self.source)

    def fake_download(self, url, allowed, out, limit, **kwargs):
        data = self.zip.read_bytes()
        out.write(data)
        return len(data)

    def test_numeric_version_order(self):
        self.assertGreater(w.version_key("0.10.0"), w.version_key("0.2.99"))
        for version in ("v1.0.0", "01.0.0", "1.0", "1.0.0-beta", "../1.0.0", None):
            with self.subTest(version=version), self.assertRaises(w.WorkshopError):
                w.version_key(version)

    def test_feed_validation(self):
        feed = {"schema_version": 1, "product": w.PRODUCT, "latest": self.latest}
        self.assertEqual(w.validate_feed(feed, "https://portfolio.example/feed.json"), self.latest)
        for change in ({"size": True}, {"size": w.MAX_DOWNLOAD + 1}, {"sha256": "x" * 64}, {"url": "https://unrelated.example/x"}, {"mirrors": ["https://evil.example/a.zip"]}, {"mirrors": "bad"}):
            with self.subTest(change=change), self.assertRaises(w.WorkshopError):
                w.validate_feed({**feed, "latest": {**self.latest, **change}}, "https://portfolio.example/feed.json")

    def test_url_origin_rules(self):
        for url in ("http://portfolio.example/a", "https://u:p@portfolio.example/a", "https://portfolio.example:8443/a", "https://portfolio.example/a#fragment", "file:///x", None):
            with self.subTest(url=url), self.assertRaises(w.WorkshopError):
                w.origin(url)

    def test_redirect_rejects_downgrade_and_external(self):
        handler = w.SafeRedirect({"https://portfolio.example"})
        req = w.urllib.request.Request("https://portfolio.example/a")
        for url in ("http://portfolio.example/b", "https://evil.example/b"):
            with self.assertRaises(w.WorkshopError):
                handler.redirect_request(req, None, 302, "Found", {}, url)
        self.assertEqual(handler.redirect_request(req, None, 302, "Found", {}, "https://portfolio.example/b").full_url, "https://portfolio.example/b")

    def test_bad_size_and_hash_leave_source(self):
        before = w.tree_hashes(self.source)
        for latest in ({**self.latest, "size": self.latest["size"] + 1}, {**self.latest, "sha256": "0" * 64}):
            with self.assertRaises(w.WorkshopError):
                self.activate(latest=latest)
        self.assertEqual(w.tree_hashes(self.source), before)
        self.assertIsNone(w.active_release(self.home))

    def test_real_upgrade_and_child_dispatch(self):
        before = w.tree_hashes(self.source)
        active = self.activate()
        self.assertEqual(w.release_version(active), "0.2.0")
        result = subprocess.run([sys.executable, "-B", str(self.source / "cog_workshop.py"), "--offline", "--home", str(self.home), "version"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "0.2.0")
        self.assertEqual(w.tree_hashes(self.source), before)
        self.assertEqual(w.active_release(self.home), active)

    def test_downgrade_and_same_version_rejected(self):
        self.activate()
        with self.assertRaises(w.WorkshopError):
            self.activate()
        package, latest = self.make_package("0.1.0")
        with self.assertRaises(w.WorkshopError):
            self.activate(package, latest)

    def test_failed_activation_retains_old_then_recovers_orphan(self):
        old = self.activate()
        package, latest = self.make_package("0.3.0")
        original = w.atomic_json
        def fail_pointer(path, value):
            if Path(path).name == "active.json":
                raise OSError("simulated pointer replacement failure")
            return original(path, value)
        with mock.patch.object(w, "atomic_json", side_effect=fail_pointer), self.assertRaises(OSError):
            self.activate(package, latest)
        self.assertEqual(w.active_release(self.home), old)
        new = self.activate(package, latest)
        self.assertEqual(w.release_version(new), "0.3.0")
        self.assertEqual(w.read_json(self.home / "active.previous.json")["version"], "0.2.0")

    def test_corrupt_pointer_and_modified_release_recover_previous(self):
        old = self.activate()
        package, latest = self.make_package("0.3.0")
        new = self.activate(package, latest)
        (self.home / "active.json").write_text("{broken", encoding="utf-8")
        self.assertEqual(w.active_release(self.home), old)
        w.atomic_json(self.home / "active.json", {"version": "0.3.0"})
        (new / "cog_workshop.py").write_text("changed", encoding="utf-8")
        self.assertEqual(w.active_release(self.home), old)
        self.assertEqual((new / "cog_workshop.py").read_text(), "changed")

    def test_existing_modified_orphan_preserved(self):
        self.home.mkdir()
        orphan = self.home / "versions/0.2.0"
        shutil.copytree(self.base / "tree-0.2.0", orphan)
        w.atomic_json(orphan / ".verified-install.json", {"sha256": self.latest["sha256"]})
        (orphan / "user.txt").write_text("preserve")
        with self.assertRaises(w.WorkshopError):
            self.activate()
        self.assertEqual((orphan / "user.txt").read_text(), "preserve")

    def test_version_mismatch_does_not_activate(self):
        with self.assertRaises(w.WorkshopError):
            self.activate(latest={**self.latest, "version": "0.9.0"})
        self.assertIsNone(w.active_release(self.home))

    def test_archive_dangerous_paths(self):
        for name in ("../evil", "/abs", "C:/evil", "a\\evil", "a/../b", "a//b", "a/CON.txt", "a/trailing.", "a/stream:ads", "a/NUL", "a/evil\t"):
            with self.subTest(name=name):
                output = io.BytesIO()
                with zipfile.ZipFile(output, "w") as archive:
                    archive.writestr(name.replace("\\", "/"), b"danger")
                raw = output.getvalue()
                if "\\" in name:
                    # ZipInfo normalizes os.sep on Windows at write time; exercise a raw hostile ZIP instead.
                    raw = raw.replace(name.replace("\\", "/").encode(), name.encode())
                with zipfile.ZipFile(io.BytesIO(raw)) as archive, self.assertRaises(w.WorkshopError):
                    w.safe_members(archive)

    def test_archive_case_unicode_and_parent_collisions(self):
        for names in (("A.txt", "a.txt"), ("A/x", "a/y"), ("café/x", "cafe\u0301/y"), ("thing", "thing/x")):
            with self.subTest(names=names):
                output = io.BytesIO()
                with zipfile.ZipFile(output, "w") as archive:
                    for name in names:
                        archive.writestr(name, b"x")
                with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive, self.assertRaises(w.WorkshopError):
                    w.safe_members(archive)

    def test_archive_symlink_rejected(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            item = zipfile.ZipInfo("link")
            item.create_system = 3
            item.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(item, "../outside")
        with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive, self.assertRaises(w.WorkshopError):
            w.safe_members(archive)

    def test_archive_expansion_and_entry_bounds(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("a", b"x" * 100)
        for constant, value in (("MAX_FILES", 0), ("MAX_EXTRACTED", 10)):
            with mock.patch.object(w, constant, value), zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive, self.assertRaises(w.WorkshopError):
                w.safe_members(archive)

    def test_update_check_only_never_downloads(self):
        with mock.patch.object(w, "read_feed", return_value=self.latest), mock.patch.object(w, "stream_url") as download:
            result = w.update(self.home, "https://portfolio.example/feed", check_only=True, source_root=self.source)
        self.assertEqual(result["status"], "available")
        download.assert_not_called()
        self.assertIsNone(w.active_release(self.home))

    def test_update_success_and_opt_in_absence(self):
        with mock.patch.object(w, "read_feed", return_value=self.latest), mock.patch.object(w, "stream_url", side_effect=self.fake_download):
            result = w.update(self.home, "https://portfolio.example/feed", source_root=self.source)
        self.assertEqual(result["status"], "updated")
        self.assertEqual(result["skill"]["status"], "not-opted-in")

    def test_automatic_invocation_upgrades_and_runs_active(self):
        child_results = []
        original_run = subprocess.run
        def run_child(command):
            child = original_run(command, text=True, capture_output=True)
            child_results.append(child)
            return child.returncode
        with mock.patch.object(w, "ROOT", self.source), mock.patch.object(w, "read_feed", return_value=self.latest), mock.patch.object(w, "stream_url", side_effect=self.fake_download), mock.patch.object(w.subprocess, "call", side_effect=run_child), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(w.main(["--home", str(self.home), "version"]), 0)
        self.assertEqual(len(child_results), 1)
        self.assertEqual(child_results[0].stdout.strip(), "0.2.0", child_results[0].stderr)
        self.assertFalse(w.auto_due(self.home, 86400))

    def test_stream_download_bounds(self):
        class Response(io.BytesIO):
            url = "https://portfolio.example/a"
            headers = {}
        opener = mock.Mock()
        opener.open.return_value = Response(b"123456")
        with mock.patch.object(w.urllib.request, "build_opener", return_value=opener), self.assertRaises(w.WorkshopError):
            w.stream_url(Response.url, {"https://portfolio.example"}, io.BytesIO(), 5)
        opener.open.return_value = Response(b"x")
        opener.open.return_value.headers = {"Content-Length": "99"}
        with mock.patch.object(w.urllib.request, "build_opener", return_value=opener), self.assertRaises(w.WorkshopError):
            w.stream_url(Response.url, {"https://portfolio.example"}, io.BytesIO(), 5)

    def test_stream_deadline(self):
        class Response(io.BytesIO):
            url = "https://portfolio.example/a"
            headers = {}
        opener = mock.Mock()
        opener.open.return_value = Response(b"x")
        with mock.patch.object(w.urllib.request, "build_opener", return_value=opener), mock.patch.object(w.time, "monotonic", side_effect=[0, 100]), self.assertRaises(w.WorkshopError):
            w.stream_url(Response.url, {"https://portfolio.example"}, io.BytesIO(), 5, deadline=10)

    def test_failed_network_retains_work_and_attempt_interval(self):
        marker = self.source / "my-level.cog"
        marker.write_text("user work")
        with mock.patch.object(w, "read_feed", side_effect=OSError("offline")), self.assertRaises(OSError):
            w.update(self.home, source_root=self.source)
        self.assertEqual(marker.read_text(), "user work")
        self.assertFalse(w.auto_due(self.home, 86400))

    def test_failed_download_keeps_active(self):
        active = self.activate()
        _, latest = self.make_package("0.3.0")
        with mock.patch.object(w, "read_feed", return_value=latest), mock.patch.object(w, "stream_url", side_effect=OSError("interrupted")), self.assertRaises(w.WorkshopError):
            w.update(self.home, source_root=self.source)
        self.assertEqual(w.active_release(self.home), active)

    def test_skill_opt_in_refresh_and_backup(self):
        target = self.base / "skills/public"
        first = w.install_skill(self.home, self.source, target)
        previous = (target / "SKILL.md").read_bytes()
        active = self.activate()
        second = w.sync_installed_skill(self.home, active)
        self.assertEqual(second["status"], "installed")
        self.assertEqual(second["version"], "0.2.0")
        self.assertEqual((Path(second["backup"]) / "SKILL.md").read_bytes(), previous)
        self.assertNotEqual((target / "SKILL.md").read_bytes(), previous)

    def test_skill_modified_or_unrelated_preserved(self):
        target = self.base / "skills/public"
        target.mkdir(parents=True)
        (target / "private.cog").write_text("private work")
        with self.assertRaises(w.WorkshopError):
            w.install_skill(self.home, self.source, target)
        self.assertEqual((target / "private.cog").read_text(), "private work")
        other = self.base / "skills/managed"
        w.install_skill(self.home, self.source, other)
        (other / "SKILL.md").write_text("user edits")
        result = w.sync_installed_skill(self.home, self.activate())
        self.assertEqual(result["status"], "preserved")
        self.assertEqual((other / "SKILL.md").read_text(), "user edits")

    def test_skill_failed_rename_restores_backup(self):
        target = self.base / "skills/public"
        w.install_skill(self.home, self.source, target)
        before = w.tree_hashes(target)
        original = os.replace
        def fail_stage(source, dest):
            if Path(source).name.startswith(".cog-skill-"):
                raise OSError("simulated stage rename failure")
            return original(source, dest)
        with mock.patch.object(w.os, "replace", side_effect=fail_stage), self.assertRaises(OSError):
            w.install_skill(self.home, self.source, target)
        self.assertEqual(w.tree_hashes(target), before)

    def test_offline_cli_never_calls_network(self):
        with mock.patch.object(w, "ROOT", self.source), mock.patch.object(w, "update") as update, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(w.main(["--offline", "--home", str(self.home), "version"]), 0)
            update.assert_not_called()
        with mock.patch.object(w, "ROOT", self.source), mock.patch.object(w, "update") as update, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(w.main(["--offline", "--home", str(self.home), "update"]), 2)
            update.assert_not_called()

    def test_lock_excludes_concurrent_update(self):
        with w.update_lock(self.home):
            command = [sys.executable, "-B", "-c", "from pathlib import Path; from tools.workshop import update_lock; import sys;\nwith update_lock(Path(sys.argv[1])): print('locked')", str(self.home)]
            result = subprocess.run(command, cwd=w.ROOT, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already running", result.stderr)


if __name__ == "__main__":
    unittest.main()
