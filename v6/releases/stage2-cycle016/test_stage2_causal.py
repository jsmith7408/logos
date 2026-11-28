import unittest
from stage2_causal import causal
from stage2_unified import dispatch
M=[{'name':'A','parents':[],'table':[False]},{'name':'B','parents':['A'],'table':[False,True]},{'name':'C','parents':['A','B'],'table':[False,False,False,True]}]
class CausalTests(unittest.TestCase):
    def test_chain(self): self.assertTrue(causal(M,{'A':True},'C')['counterfactual'])
    def test_cut(self): self.assertFalse(causal(M,{'A':True,'B':False},'C')['counterfactual'])
    def test_factual(self): self.assertFalse(causal(M,{},'C')['changed'])
    def test_cycle(self):
        with self.assertRaises(ValueError): causal(M[::-1],{},'C')
    def test_invalid(self):
        with self.assertRaises(ValueError): causal(M,{'A':1},'C')
    def test_dispatch(self): self.assertEqual(dispatch({'operation':'causal','input':{'model':M,'intervention':{},'query':'C'}})['status'],'solved')
