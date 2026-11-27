from test_knowledge import Tests as Base
import unittest
class Scoped(unittest.TestCase):
    setUp=Base.setUp
    tearDown=Base.tearDown
    def test_unrelated_conflict(self):
        self.k.fact('A','s'); self.k.fact('X','s'); self.k.fact('!X','s'); self.k.rule(['A'],'B')
        self.assertEqual(self.k.infer('B',isolate=True)['status'],'supported')
        self.assertEqual(self.k.infer('B')['status'],'conflict')
    def test_relevant_conflict(self):
        self.k.fact('A','s'); self.k.fact('X','s'); self.k.rule(['X'],'!A'); self.k.rule(['A'],'B')
        self.assertEqual(self.k.infer('B',isolate=True)['status'],'conflict')
    def test_scoped_budget(self):
        self.k.rule(['A'],'B'); self.assertEqual(self.k.infer('B',1,isolate=True)['status'],'budget_exhausted')
    def test_route(self):
        from strategy import Strategy
        from bridge import Application
        s=Strategy(Application(self.core,None)); s.collective.run=lambda *a,**k:self.fail('provider invoked')
        self.k.fact('A','s'); self.assertEqual(s.run('infer-local:A')['conclusion'],'supported')
del Base
