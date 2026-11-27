import json,tempfile
from core import Core
from bridge import Application
from strategy import Strategy
from language30 import Language30

def run():
    with tempfile.TemporaryDirectory() as d:
        c=Core(d+'/db'); l=Language30(Strategy(Application(c,None)))
        for split,text in [('train','logos learns logic. logos learns facts. research tests evidence. '*8),('train','research learns logic. logos tests evidence. research learns facts. '*7),('validation','logos learns evidence. research tests logic. logos learns facts.'),('test','research learns evidence. logos tests logic. research tests facts.')]:
            l.add(text,'synthetic '+split,split,approved=True)
        r=l.train(30112601,24,4); g=None
        if r['eligible']: l.activate(r['checkpoint'],approved=True); g=l.generate('logos learns')
        c.close(); return {'experiment':r,'generation':g,'independent':False,'note':'synthetic related sentences; final test used once for candidate admission, not independent external evaluation'}
if __name__=='__main__': print(json.dumps(run(),indent=2,allow_nan=False))
