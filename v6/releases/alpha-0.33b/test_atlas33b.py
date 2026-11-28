import unittest,tempfile,zipfile,json
from pathlib import Path
from atlas33b import ingest,search,PREFIX
class ProvenanceTests(unittest.TestCase):
    def test_metadata_change(self):
        with tempfile.TemporaryDirectory() as d:
            z=Path(d)/'a.zip'; db=Path(d)/'a.db'
            def write(name):
                with zipfile.ZipFile(z,'w') as f:
                    f.writestr(PREFIX+'sources.json',json.dumps([dict(name=name,sha256='a'*64,genre='test')]))
                    f.writestr(PREFIX+'records.jsonl',json.dumps(dict(s=0,loc='1',text='gradient descent',tags=['math'])))
            write('original'); a=ingest(db,z); self.assertEqual(ingest(db,z)['inserted'],0)
            write('changed'); b=ingest(db,z); self.assertNotEqual(a['digest'],b['digest']); self.assertEqual(b['inserted'],1)
            self.assertEqual({r['source'] for r in search(db,'gradient')},{'original','changed'})
            self.assertTrue(all(r['status']=='unverified' for r in search(db,'gradient')))
