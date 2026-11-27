import unittest,tempfile
from pathlib import Path
from core import Core,DemoProvider
class Tests(unittest.TestCase):
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'research.db'; c=Core(p); r=c.investigate('gravity',DemoProvider()); c.close(); c=Core(p); self.assertEqual(c.search('gravity'),[r]); c.close()
    def test_demo_label(self):
        c=Core(':memory:'); self.assertEqual(c.investigate('x',DemoProvider())['provenance'],'demo'); c.close()
    def test_invalid(self):
        c=Core(':memory:'); self.assertRaises(ValueError,c.investigate,' ',DemoProvider()); self.assertEqual(c.search(''),[]); c.close()
    def test_provider_failure(self):
        class Broken:
            def reason(self,q): raise RuntimeError('failure')
        c=Core(':memory:'); self.assertRaises(RuntimeError,c.investigate,'x',Broken()); self.assertEqual(c.search(''),[]); c.close()
    def test_literal_search(self):
        c=Core(':memory:'); c.investigate('gravity',DemoProvider()); self.assertEqual(c.search("' OR 1=1 --"),[]); c.close()
