import unittest,tempfile,sqlite3
from pathlib import Path
from core import Core,DemoProvider,AuthorizationError
class Tests(unittest.TestCase):
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'research.db'
            with Core(p) as c: r=c.investigate('gravity',DemoProvider())
            with Core(p) as c: self.assertEqual(c.search('gravity'),[r])
    def test_demo_label(self):
        with Core(':memory:') as c: self.assertEqual(c.investigate('x',DemoProvider())['provenance'],'demo')
    def test_invalid(self):
        with Core(':memory:') as c:
            self.assertRaises(ValueError,c.investigate,' ',DemoProvider()); self.assertEqual(c.search(''),[])
    def test_provider_failure(self):
        class Broken:
            def reason(self,q): raise RuntimeError('failure')
        with Core(':memory:') as c:
            self.assertRaises(RuntimeError,c.investigate,'x',Broken()); self.assertEqual(c.search(''),[])
    def test_literal_search(self):
        with Core(':memory:') as c:
            c.investigate('gravity',DemoProvider()); self.assertEqual(c.search("' OR 1=1 --"),[])
    def test_unauthorized_not_called(self):
        calls=[]
        class Other:
            def reason(self,q): calls.append(q); return 'bad'
        with Core(':memory:') as c:
            self.assertRaises(AuthorizationError,c.investigate,'x',Other()); self.assertEqual(c.search(''),[])
        self.assertEqual(calls,[])
    def test_subclass(self):
        class Other(DemoProvider):
            def reason(self,q): self.fail('called')
        with Core(':memory:') as c: self.assertRaises(AuthorizationError,c.investigate,'x',Other())
    def test_override(self):
        p=DemoProvider(); p.reason=lambda q: self.fail('called')
        with Core(':memory:') as c: self.assertRaises(AuthorizationError,c.investigate,'x',p)
    def test_forged_write(self):
        with Core(':memory:') as c:
            r=c.prepare('x',DemoProvider()); r['provenance']='verified'
            self.assertRaises(AuthorizationError,c.insert,r); self.assertEqual(c.search(''),[])
    def test_close(self):
        with Core(':memory:') as c: pass
        c.close(); self.assertRaises(sqlite3.ProgrammingError,c.search,'')
    def test_rollback(self):
        with Core(':memory:') as c:
            r=c.prepare('x',DemoProvider())
            with self.assertRaises(sqlite3.IntegrityError):
                with c.db: c.insert(r); c.insert(r)
            self.assertEqual(c.search(''),[])
