"""Alpha 0.32 native runtime; experimental records are not V5 evidence."""
import argparse,json,hmac,hashlib
from runtime31 import keyfile
from orchestration31 import run
from audit31 import retrieve
from memory import Memory
from core import Core,DemoProvider
VERSION='V6.0 Alpha 0.32'
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--version',action='version',version=VERSION); p.add_argument('--key',required=True); p.add_argument('--db',required=True)
    s=p.add_subparsers(dest='cmd',required=True); s.add_parser('init'); s.add_parser('solve').add_argument('question'); s.add_parser('retrieve').add_argument('id'); s.add_parser('demo').add_argument('question'); s.add_parser('memory-get').add_argument('id'); q=s.add_parser('remember'); q.add_argument('claim'); q.add_argument('--source',required=True); q.add_argument('--dependency',action='append',default=[]); q.add_argument('--contradicts',action='append',default=[])
    a=p.parse_args(argv)
    if a.cmd=='init': keyfile(a.key,True); r={'initialized':True}
    else:
        key=keyfile(a.key)
        if a.cmd=='solve': r=run(a.db,a.question,key)
        elif a.cmd=='retrieve': r=retrieve(a.db,a.id,key)
        elif a.cmd=='demo':
            with Core(a.db) as c: r=c.investigate(a.question,DemoProvider())
        else:
            m=Memory(a.db,hmac.new(key,b'LOGOS32-memory',hashlib.sha256).digest())
            r=m.get(a.id) if a.cmd=='memory-get' else m.append(a.claim,a.source,a.dependency,a.contradicts)
    print(json.dumps(r,allow_nan=False))
if __name__=='__main__': main()
