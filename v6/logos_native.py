"""Native-only command line; no provider arguments or third-party model imports at invocation."""
import argparse,json
from pathlib import Path
from core import Core
from bridge import Application
from strategy import Strategy
from native_research import evaluate

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--db',default='research.sqlite'); sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('status'); q=sub.add_parser('solve'); q.add_argument('task'); q=sub.add_parser('objective'); q.add_argument('literal'); q=sub.add_parser('cycle'); q.add_argument('--seed',type=int,default=28112601); q.add_argument('--limit',type=int,default=4)
    q=sub.add_parser('train'); q.add_argument('corpus'); q=sub.add_parser('predict'); q.add_argument('start'); q=sub.add_parser('fetch'); q.add_argument('url'); q.add_argument('--allow-host',required=True,action='append'); q=sub.add_parser('benchmark'); q.add_argument('dataset'); q.add_argument('--source',required=True)
    q=sub.add_parser('learn'); q.add_argument('corpus'); q.add_argument('--source',required=True); q.add_argument('--approve',action='store_true')
    q=sub.add_parser('review-web'); q.add_argument('snapshot'); q.add_argument('excerpt'); q.add_argument('--approve',action='store_true')
    q=sub.add_parser('train-neural'); q.add_argument('--seed',type=int,default=29112601); q.add_argument('--epochs',type=int,default=12)
    q=sub.add_parser('activate-neural'); q.add_argument('checkpoint'); q.add_argument('--approve',action='store_true')
    q=sub.add_parser('generate'); q.add_argument('prompt'); q=sub.add_parser('similar'); q.add_argument('word'); q=sub.add_parser('chat'); q.add_argument('text')
    a=p.parse_args(); c=Core(a.db)
    try:
        s=Strategy(Application(c,None)); n=s.native
        from language29 import Language29
        lang=Language29(s)
        if a.cmd=='learn':
            with open(a.corpus,encoding='utf-8') as f: r={'corpus_id':lang.add(f.read(40001),a.source,approved=a.approve)}
        elif a.cmd=='review-web': r={'corpus_id':lang.approve_web(a.snapshot,a.excerpt,approved=a.approve)}
        elif a.cmd=='train-neural': r=lang.train(a.seed,a.epochs)
        elif a.cmd=='activate-neural': lang.activate(a.checkpoint,approved=a.approve); r={'active':a.checkpoint}
        elif a.cmd=='generate': r=lang.generate(a.prompt)
        elif a.cmd=='similar': r=lang.similar(a.word)
        elif a.cmd=='chat': r=lang.converse(a.text)
        elif a.cmd=='status': r=n.status()
        elif a.cmd=='solve': r=n.transfer(json.loads(a.task))
        elif a.cmd=='objective': r={'objective':s.planner.create(a.literal)}
        elif a.cmd=='cycle': r=n.cycle(a.seed,a.limit)
        elif a.cmd=='train':
            with open(a.corpus,encoding='utf-8') as f: r=n.train_language(f.read(40001))
        elif a.cmd=='predict': r=n.predict(a.start)
        elif a.cmd=='fetch': r=n.fetch(a.url,a.allow_host)
        elif a.cmd=='benchmark':
            with open(a.dataset,encoding='utf-8') as f: raw=f.read(262145)
            if len(raw)>262144: raise ValueError('benchmark input limit')
            r=n.import_benchmark(json.loads(raw),a.source)
        print(json.dumps(r,indent=2,allow_nan=False))
    finally: c.close()
if __name__=='__main__': main()
