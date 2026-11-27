import unittest
from tokenizer31 import BytePair

class Tests(unittest.TestCase):
    def test_roundtrip(self):
        m=BytePair.train(['hello hello']*3)
        for s in ['', 'hello', '未知 🌍', 'a\x00b']:
            self.assertEqual(m.decode(m.encode(s)),s)
    def test_compression(self):
        m=BytePair.train(['abc abc abc']*3)
        self.assertLess(len(m.encode('abc abc abc')),11)
    def test_determinism(self):
        self.assertEqual(BytePair.train(['ab ab','cd cd']).merges,BytePair.train(['cd cd','ab ab']).merges)
    def test_invalid_rule(self):
        with self.assertRaises(ValueError): BytePair([(256,0)])
    def test_invalid_token(self):
        with self.assertRaises(ValueError): BytePair().decode([256])
    def test_budget(self):
        with self.assertRaises(ValueError): BytePair.train(['a'*65537])
    def test_no_cross_document(self):
        self.assertEqual(BytePair.train(['a','b']*3).merges,())

if __name__=='__main__': unittest.main()
