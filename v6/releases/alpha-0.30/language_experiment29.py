"""Reproducible own-weight training smoke test, not independent validation."""
import tempfile,json
from core import Core
from bridge import Application
from strategy import Strategy
from language29 import Language29,examples,tokenize

def run():
    with tempfile.TemporaryDirectory() as d:
        c=Core(d+'/experiment.db'); l=Language29(Strategy(Application(c,None)))
        corpus='logos learns logic. logos learns facts. research tests evidence. '*12
        l.add(corpus,'synthetic developer corpus',approved=True)
        r=l.train(29112601,20); l.activate(r['checkpoint'],approved=True)
        m=l.load(); test='research learns facts. logos tests evidence.'
        report={'training':r,'generation':l.generate('logos learns'),'similarity':l.similar('logic'),'novel_recombination':{'text':test,'loss':m.loss(examples(tokenize(test),m.vocab)),'independent':False},'provider_attempts':0}
        c.close(); return report
if __name__=='__main__': print(json.dumps(run(),indent=2,allow_nan=False))
