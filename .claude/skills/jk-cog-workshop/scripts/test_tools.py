"""Offline behavioral checks for the passive importer and target preflight."""
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from import_local import Importer
from inspect_cog import inspect

COG=b'symbols\nmessage onStart=startup\nthing subject=-1 local\nend\ncode\nonStart:\nGetThingGUID(subject);\nreturn;\nend\n'

def gob(name='cog/example.cog',data=COG):
    offset=12+len(data)
    return struct.pack('<4sII',b'GOB ',20,offset)+data+struct.pack('<I',1)+struct.pack('<Ii128s',12,len(data),name.encode().ljust(128,b'\0'))

class Tools(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def run_import(self,data,name):
        imp=Importer(self.root,'jk');h=hashlib.sha256(data).hexdigest()
        imp.walk(io.BytesIO(data),len(data),name,[{'name':name,'sha256':h,'bytes':len(data)}],0)
        return imp
    def test_gob_bytes_and_chain(self):
        data=gob();imp=self.run_import(data,'example.gob');self.assertEqual(len(imp.cogs),1)
        h=hashlib.sha256(COG).hexdigest();row=imp.cogs[h]
        self.assertEqual((self.root/row['object_path']).read_bytes(),COG)
        chain=row['provenance'][0]['chain'];self.assertEqual(chain[-1]['offset'],12);self.assertEqual(chain[-1]['sha256'],h)
        self.assertEqual(chain[-1]['container_sha256'],hashlib.sha256(data).hexdigest())
    def test_nested_zip_preserves_both_container_identities(self):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('inside.goo',gob())
        imp=self.run_import(buf.getvalue(),'pack.zip');row=next(iter(imp.cogs.values()))
        chain=row['provenance'][0]['chain'];self.assertEqual(len(chain),3)
        self.assertEqual(chain[1]['sha256'],hashlib.sha256(gob()).hexdigest());self.assertIn('crc32',chain[1])
    def test_gob_out_of_bounds_rejected(self):
        data=bytearray(gob());directory=struct.unpack_from('<I',data,8)[0]
        struct.pack_into('<I',data,directory+4,len(data)+100)
        with self.assertRaisesRegex(ValueError,'extent'):self.run_import(bytes(data),'bad.gob')
        self.assertFalse((self.root/'objects').exists())
    def test_gob_directory_overlap_rejected(self):
        data=bytearray(gob());directory=struct.unpack_from('<I',data,8)[0]
        struct.pack_into('<i',data,directory+8,len(COG)+10)
        with self.assertRaisesRegex(ValueError,'overlaps directory'):self.run_import(bytes(data),'bad.gob')
    def test_traversal_rejected_without_writes(self):
        with self.assertRaisesRegex(ValueError,'Unsafe'):self.run_import(gob('../escape.cog'),'bad.goo')
        self.assertFalse((self.root/'objects').exists())
    def test_non_cog_member_not_extracted(self):
        imp=self.run_import(gob('program.exe',b'MZarbitrary'),'pack.gob')
        self.assertFalse(imp.cogs);self.assertFalse((self.root/'objects').exists())
    def test_hash_collision_or_corruption_not_overwritten(self):
        h=hashlib.sha256(COG).hexdigest();path=self.root/'objects'/h[:2]/(h+'.cog');path.parent.mkdir(parents=True);path.write_bytes(b'wrong')
        imp=self.run_import(gob(),'example.gob');self.assertEqual(len(imp.errors),1);self.assertEqual(path.read_bytes(),b'wrong')
    def test_target_and_alias_preflight(self):
        p=self.root/'sample.cog';p.write_bytes(COG);jk=inspect(p,'jk');mots=inspect(p,'mots')
        self.assertEqual([x['name'] for x in jk['calls_absent_from_target_registry']],['getthingguid'])
        self.assertFalse(mots['calls_absent_from_target_registry']);self.assertEqual(jk['declared_messages'],['startup']);self.assertFalse(jk['messages_absent_from_target_registry'])
    def test_explicit_cli_import_and_source_lookup(self):
        path=self.root/'owned.gob';path.write_bytes(gob());out=self.root/'private';scripts=Path(__file__).parent
        imported=subprocess.run([sys.executable,str(scripts/'import_local.py'),'--game','jk','--out',str(out),str(path)],capture_output=True,text=True)
        self.assertEqual(imported.returncode,0,imported.stderr);self.assertTrue((out/'PRIVATE_LOCAL_CORPUS').is_file())
        shown=subprocess.run([sys.executable,str(scripts/'corpus.py'),'--root',str(out),'show',hashlib.sha256(COG).hexdigest(),'--source'],capture_output=True,text=True)
        self.assertEqual(shown.returncode,0,shown.stderr);self.assertIn('GetThingGUID(subject)',shown.stdout)
        again=subprocess.run([sys.executable,str(scripts/'import_local.py'),'--game','jk','--out',str(out),str(path)],capture_output=True,text=True)
        self.assertEqual(again.returncode,2);self.assertIn('not overwritten',again.stderr)

if __name__=='__main__':unittest.main()
