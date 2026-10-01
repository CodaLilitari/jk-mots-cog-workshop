"""Bounded synthetic workload tests; no Git process or external network."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'skill/jk-mots-cog-workflow/scripts'))
from tools import workshop as w
import import_local as local

COG=b'symbols\nmessage startup\nend\ncode\nstartup:\nreturn;\nend\n'

class WorkloadTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        self.repo=self.base/'repo';self.repo.mkdir()
        (self.repo/'.git').mkdir()
        self.out=self.base/'private'
    def tearDown(self):self.temp.cleanup()
    def pack(self,items):
        result=io.BytesIO()
        with zipfile.ZipFile(result,'w') as z:
            for name,data in items:z.writestr(name,data)
        return result.getvalue()
    def importer(self):return local.Importer(self.out,'jk')
    def walk(self,importer,data):
        return importer.walk(io.BytesIO(data),len(data),'pack.zip',[{'name':'pack.zip','sha256':hashlib.sha256(data).hexdigest()}],0)
    def test_import_rejects_repository_output_before_writing(self):
        with self.assertRaisesRegex(ValueError,'outside Git'):local.Importer(self.repo/'artifacts/private','jk')
        self.assertFalse((self.repo/'artifacts').exists())
    def test_import_cli_rejects_repository_output(self):
        source=self.base/'owned.cog';source.write_bytes(COG)
        p=subprocess.run([sys.executable,'-B',str(ROOT/'skill/jk-mots-cog-workflow/scripts/import_local.py'),'--game','jk','--out',str(self.repo/'private'),str(source)],capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,2,p.stderr);self.assertIn('outside Git',p.stderr)
        self.assertFalse((self.repo/'private').exists())
    def test_updater_rejects_repository_home_before_lock(self):
        with self.assertRaisesRegex(w.WorkshopError,'outside Git'):
            with w.update_lock(self.repo/'cache'):self.fail('Lock acquired')
        self.assertFalse((self.repo/'cache').exists())
    def test_updater_cli_rejects_repository_home(self):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(w.main(['--offline','--home',str(self.repo/'cache'),'version']),2)
        self.assertIn('outside Git',err.getvalue());self.assertFalse((self.repo/'cache').exists())
    def test_worktree_git_file_is_detected(self):
        root=self.base/'worktree';root.mkdir();(root/'.git').write_text('gitdir: elsewhere\n')
        for guard in (local.outside_checkout,w.outside_checkout):
            with self.assertRaises(Exception):guard(root/'nested/data')
    def test_linked_output_cannot_hide_repository(self):
        alias=self.base/'alias'
        if os.name=='nt':
            import _winapi
            _winapi.CreateJunction(str(self.repo),str(alias))
        else:alias.symlink_to(self.repo,target_is_directory=True)
        for guard in (local.outside_checkout,w.outside_checkout):
            with self.assertRaises(Exception):guard(alias/'private')
        with mock.patch.dict(os.environ,{'COG_WORKSHOP_HOME':str(alias/'private')}):
            with self.assertRaises(w.WorkshopError):w.outside_checkout(w.data_home())
    def test_lexical_repository_path_cannot_escape_through_link(self):
        safe=self.base/'safe';safe.mkdir();alias=self.repo/'alias'
        if os.name=='nt':
            import _winapi
            _winapi.CreateJunction(str(safe),str(alias))
        else:alias.symlink_to(safe,target_is_directory=True)
        for guard in (local.outside_checkout,w.outside_checkout):
            with self.assertRaises(Exception):guard(alias/'private')
    def test_tree_limit_stops_before_hashing_all_files(self):
        root=self.base/'tree';root.mkdir()
        for i in range(5):(root/str(i)).write_text('x')
        with mock.patch.object(w,'MAX_FILES',2),mock.patch.object(w,'sha256_file',wraps=w.sha256_file) as hashed:
            with self.assertRaisesRegex(w.WorkshopError,'too many entries'):w.tree_hashes(root)
        self.assertEqual(hashed.call_count,2)
    def test_archive_counts_implicit_directories_before_extraction(self):
        data=self.pack([('one/two/three.cog',COG)])
        with mock.patch.object(w,'MAX_FILES',2),zipfile.ZipFile(io.BytesIO(data)) as archive,self.assertRaisesRegex(w.WorkshopError,'implicit directories'):
            w.safe_members(archive)
    def test_tree_byte_limit_checks_before_read(self):
        root=self.base/'tree';root.mkdir();(root/'large').write_bytes(b'x'*100)
        with mock.patch.object(w,'MAX_EXTRACTED',10),mock.patch.object(w,'sha256_file') as hashed:
            with self.assertRaisesRegex(w.WorkshopError,'byte budget'):w.tree_hashes(root)
        hashed.assert_not_called()
    def test_discovery_limit_is_bounded(self):
        root=self.base/'inputs';root.mkdir()
        for i in range(5):(root/f'{i}.txt').write_text('x')
        with mock.patch.object(local,'MAX_DISCOVERY_ENTRIES',2),self.assertRaises(local.ImportLimit):
            local.discover_inputs([root],self.out)
        self.assertFalse(self.out.exists())
    def test_input_file_limit_is_bounded(self):
        root=self.base/'inputs';root.mkdir()
        for i in range(3):(root/f'{i}.cog').write_bytes(COG)
        with mock.patch.object(local,'MAX_INPUT_FILES',2),self.assertRaises(local.ImportLimit):
            local.discover_inputs([root],self.out)
    def test_output_cannot_be_under_input(self):
        with self.assertRaisesRegex(ValueError,'contain each other'):
            local.discover_inputs([self.repo],self.repo/'private')
    def test_global_member_limit_precedes_extraction(self):
        data=self.pack([(f'{i}.cog',COG) for i in range(3)]);imp=self.importer()
        with mock.patch.object(local,'MAX_TOTAL_MEMBERS',2),self.assertRaises(local.ImportLimit):self.walk(imp,data)
        self.assertFalse(self.out.exists())
    def test_unique_object_limit_stops_before_extra_file(self):
        data=self.pack([(f'{i}.cog',COG+b'# '+str(i).encode()) for i in range(3)]);imp=self.importer()
        with mock.patch.object(local,'MAX_UNIQUE_COGS',2),self.assertRaises(local.ImportLimit):self.walk(imp,data)
        self.assertEqual(len(list(self.out.rglob('*.cog'))),2)
    def test_occurrence_limit_also_bounds_duplicate_provenance(self):
        data=self.pack([(f'{i}.cog',COG) for i in range(3)]);imp=self.importer()
        with mock.patch.object(local,'MAX_COG_OCCURRENCES',2),self.assertRaises(local.ImportLimit):self.walk(imp,data)
        self.assertEqual(len(next(iter(imp.cogs.values()))['provenance']),2)
    def test_global_expansion_budget_is_fatal(self):
        imp=self.importer();data=self.pack([('a.cog',COG),('b.cog',COG)])
        with mock.patch.object(local,'MAX_EXPANSION',len(COG)),self.assertRaises(local.ImportLimit):self.walk(imp,data)
        self.assertEqual(imp.occurrences,1)
    def test_nested_archives_stream_without_zip_read(self):
        inner=self.pack([('a.cog',COG)])
        data=self.pack([('inner.zip',inner)]);imp=self.importer()
        with mock.patch.object(zipfile.ZipFile,'read',side_effect=AssertionError('Whole-member allocation forbidden')):
            self.walk(imp,data)
        self.assertEqual((self.out/next(iter(imp.cogs.values()))['object_path']).read_bytes(),COG)
    def test_spool_rolls_to_disk_at_small_fixture_threshold(self):
        rolled=[];original=local.tempfile.SpooledTemporaryFile
        @contextlib.contextmanager
        def tracked(*args,**kwargs):
            with original(*args,**kwargs) as stream:
                yield stream
                rolled.append(stream._rolled)
        imp=self.importer();data=self.pack([('a.cog',COG)])
        with mock.patch.object(local,'SPOOL_BYTES',8),mock.patch.object(local.tempfile,'SpooledTemporaryFile',tracked):self.walk(imp,data)
        self.assertTrue(any(rolled))
    def test_incomplete_import_returns_error_and_keeps_partial_catalog(self):
        source=self.base/'pack.zip';source.write_bytes(self.pack([(f'{i}.cog',COG+b'# '+str(i).encode()) for i in range(3)]))
        argv=['import_local.py','--game','jk','--out',str(self.out),str(source)]
        with mock.patch.object(local,'MAX_UNIQUE_COGS',2),mock.patch.object(sys,'argv',argv),contextlib.redirect_stdout(io.StringIO()),self.assertRaises(SystemExit) as stopped:
            local.main()
        self.assertEqual(stopped.exception.code,2)
        self.assertEqual(json.loads((self.out/'stats.json').read_text())['distinct_cog_bodies'],2)
        self.assertTrue(json.loads((self.out/'import-errors.json').read_text())[0]['stopped'])

if __name__=='__main__':unittest.main()
