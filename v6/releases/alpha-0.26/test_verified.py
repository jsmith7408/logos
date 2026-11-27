import unittest,sqlite3,hmac,hashlib
from types import SimpleNamespace
from acquisition import Acquisition
from knowledge import Knowledge
from verified import Verified
class TestVerified(unittest.TestCase):
    def setUp(self):
        self.s=SimpleNamespace(db=sqlite3.connect(':memory:')); self.s.knowledge=Knowledge(self.s.db); self.s.acquisition=Acquisition(self.s); self.v=Verified(self.s)
        self.v.configure('a',b'a'*32,'one'); self.v.configure('b',b'b'*32,'two')
    def add(self,s,text='A is a B'):
        k=self.v.trust[s][0]; return self.v.acquire(s,text,hmac.new(k,self.v.payload(s,text),hashlib.sha256).hexdigest())
    def test_promotion(self):
        l=self.v.literal(self.add('a')); self.assertFalse(self.v.promote(l)['eligible']); self.add('b'); self.assertTrue(self.v.promote(l)['eligible']); self.assertEqual(self.s.knowledge.infer(l)['status'],'supported')
    def test_forgery(self):
        with self.assertRaises(ValueError): self.v.acquire('a','A is a B','0'*64)
    def test_shared_origin(self):
        self.v.configure('b',b'b'*32,'one'); l=self.v.literal(self.add('a')); self.add('b'); self.assertFalse(self.v.promote(l)['eligible'])
    def test_opposition(self):
        l=self.v.literal(self.add('a')); self.add('b'); self.add('a','A is not a B'); self.assertFalse(self.v.promote(l)['eligible'])
    def test_shared_key(self):
        self.v.configure('b',b'a'*32,'two'); l=self.v.literal(self.add('a')); self.add('b'); self.assertFalse(self.v.promote(l)['eligible'])
