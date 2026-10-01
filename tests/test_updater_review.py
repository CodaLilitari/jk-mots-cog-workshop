"""Independent reviewer regressions for recovery and private-skill separation."""
import contextlib
import io
import http.server
import json
import os
from pathlib import Path
import sys
import threading
import time
import unittest
import urllib.request
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import workshop as w
import test_updater as fixtures


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.UpdaterTests(methodName='test_numeric_version_order')
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        environment = mock.patch.dict(os.environ, {
            'CODEX_HOME': str(self.fixture.base / 'isolated-codex-home'),
            'COG_WORKSHOP_HOME': str(self.fixture.home),
            'COG_CORPUS_ROOT': str(self.fixture.base / 'isolated-private-corpus'),
        })
        environment.start()
        self.addCleanup(environment.stop)

    def two_versions(self):
        old = self.fixture.activate()
        package, latest = self.fixture.make_package('0.3.0')
        new = self.fixture.activate(package, latest)
        return old, new

    def test_wrong_json_type_in_release_recovers_previous(self):
        old, new = self.two_versions()
        for value in ([], None, 'unexpected string', 7):
            with self.subTest(value=value):
                (new / 'release.json').write_text(json.dumps(value), encoding='utf-8')
                self.assertEqual(w.active_release(self.fixture.home), old)

    def test_wrong_json_type_in_receipt_recovers_previous(self):
        old, new = self.two_versions()
        for value in ([], None, 'unexpected string', 7):
            with self.subTest(value=value):
                (new / '.verified-install.json').write_text(json.dumps(value), encoding='utf-8')
                self.assertEqual(w.active_release(self.fixture.home), old)

    def test_wrong_json_type_in_skill_registration_preserves_skill(self):
        target = self.fixture.base / 'skills/public'
        w.install_skill(self.fixture.home, self.fixture.source, target)
        before = w.tree_hashes(target)
        active = self.fixture.activate()
        for value in ([], None, 'unexpected string', 7, {'target': 7}, {'target': []}):
            with self.subTest(value=value):
                (self.fixture.home / 'skill-install.json').write_text(json.dumps(value), encoding='utf-8')
                result = w.sync_installed_skill(self.fixture.home, active)
                self.assertEqual(result['status'], 'preserved')
                self.assertEqual(w.tree_hashes(target), before)

    def test_default_install_keeps_private_skill_and_private_corpus(self):
        codex = self.fixture.base / 'codex-home'
        private = codex / 'skills/jk-mots-cog-workflow'
        private.mkdir(parents=True)
        (private / 'SKILL.md').write_text('private skill sentinel', encoding='utf-8')
        corpus = self.fixture.base / 'private-corpus'
        corpus.mkdir()
        (corpus / 'private.cog').write_text('private corpus sentinel', encoding='utf-8')
        before = (w.tree_hashes(private), w.tree_hashes(corpus))
        with mock.patch.dict(os.environ, {'CODEX_HOME': str(codex), 'COG_CORPUS_ROOT': str(corpus)}):
            result = w.install_skill(self.fixture.home, self.fixture.source)
        self.assertEqual(Path(result['target']), codex / 'skills/jk-mots-cog-workflow-public')
        self.assertEqual((w.tree_hashes(private), w.tree_hashes(corpus)), before)

    def test_automatic_network_failure_still_runs_original_and_keeps_private_corpus(self):
        corpus = self.fixture.base / 'private-corpus'
        corpus.mkdir()
        (corpus / 'private.cog').write_text('private corpus sentinel', encoding='utf-8')
        before = w.tree_hashes(corpus)
        out = io.StringIO()
        err = io.StringIO()
        with mock.patch.dict(os.environ, {'COG_CORPUS_ROOT': str(corpus)}), mock.patch.object(w, 'ROOT', self.fixture.source), mock.patch.object(w, 'read_feed', side_effect=OSError('offline fixture')), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            result = w.main(['--home', str(self.fixture.home), 'version'])
        self.assertEqual(result, 0)
        self.assertEqual(out.getvalue().strip(), '0.0.1')
        self.assertIn('offline fixture', err.getvalue())
        self.assertEqual(w.tree_hashes(corpus), before)

    def test_trickled_response_does_not_hold_read_past_deadline(self):
        # Use real HTTPResponse buffering against loopback. Only URL authority
        # is adapted; this isolates streaming behavior, not HTTPS verification.
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Length', '40')
                self.end_headers()
                try:
                    for _ in range(40):
                        self.wfile.write(b'x')
                        self.wfile.flush()
                        time.sleep(0.03)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass

            def log_message(self, *args):
                pass

        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            response = urllib.request.urlopen('http://127.0.0.1:' + str(server.server_port), timeout=0.25)
            response.url = 'https://portfolio.example/slow-response'
            opener = mock.Mock()
            opener.open.return_value = response
            started = time.monotonic()
            with mock.patch.object(w.urllib.request, 'build_opener', return_value=opener), self.assertRaises(w.WorkshopError):
                w.stream_url(response.url, {'https://portfolio.example'}, io.BytesIO(), 100, timeout=0.25, deadline=0.08)
            elapsed = time.monotonic() - started
            self.assertLess(elapsed, 0.7, 'The read accumulated trickled bytes for longer than the deadline and socket timeout')
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
