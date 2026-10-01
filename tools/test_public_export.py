"""Regression checks for the exporter publication boundary, with synthetic data."""
import unittest
from export_public_corpus import source_record, safe_url, member_name, adapt_note

class PublicExport(unittest.TestCase):
    def test_only_bibliographic_fields_survive(self):
        row={'url':'https://www.massassi.net/levels/files/7.shtml','title':'Published title','author':'Credited author','bytes':3,'sha256':'a'*64,'status':200,
             'body':'PRIVATE BODY MUST NOT SURVIVE','raw_path':'PRIVATE PATH MUST NOT SURVIVE','capture':{'id':'PRIVATE MESSAGE'},'origins':[{'message_id':'PRIVATE ORIGIN'}],'local_path':'PRIVATE LOCAL','token':'PRIVATE TOKEN'}
        out=source_record(row,'public-test')
        self.assertEqual(out['title'],'Published title');self.assertEqual(out['sha256'],'a'*64)
        self.assertFalse(any(k in out for k in ('body','raw_path','capture','origins','local_path','token')))
        self.assertNotIn('PRIVATE',str(out))
    def test_private_host_and_signed_query_not_allowed(self):
        fake_private_url='https://'+'discord.com'+'/'+'channels'+'/123/456'
        self.assertIsNone(safe_url(fake_private_url))
        self.assertIsNone(safe_url('https://www.massassi.net/a.zip'+'?'+'token=secret'))
        self.assertIsNone(safe_url('https://www.massassi.net/a.zip?unknown=secret'))
        self.assertIsNone(safe_url('https://drive.google.com/file/d/opaque-id/view'))
        self.assertIsNone(safe_url('https://user:secret@www.massassi.net/a.zip'))
    def test_archived_public_url_keeps_source_identity(self):
        url='https://web.archive.org/web/20010206081215id_/http://eah-triscuit.com/cogs.html'
        self.assertEqual(safe_url(url),url)
        fake_private_url='https://'+'discord.com'+'/'+'channels'+'/123'
        self.assertIsNone(safe_url('https://web.archive.org/web/20010206081215id_/'+fake_private_url))
    def test_note_version_cannot_self_approve(self):
        with self.assertRaisesRegex(ValueError,'fresh publication review'):
            adapt_note('checksums-and-retail.md',b'Changed source note')
    def test_metadata_status_is_not_assumed_acquisition(self):
        r=source_record({'url':'https://www.massassi.net/a.zip','status':'http_error','http_status':404},'test')
        self.assertEqual(r['observed_status'],404);self.assertEqual(r['retrieval_state'],'http_error');self.assertNotIn('sha256',r)
    def test_member_names_exclude_filesystem_escape(self):
        self.assertIsNone(member_name('../secret.cog'));self.assertIsNone(member_name('D:/secret.cog'))
        self.assertEqual(member_name('cog\\door.cog'),'cog/door.cog')

if __name__=='__main__':unittest.main()
