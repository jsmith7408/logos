"""Own-weight two-token context neural model, bounded, no external inference.
Training is operator-authorized text modeling, not fact promotion.
"""
import re, math, random, json, hashlib
from collections import Counter
from knowledge import atom

TOKEN=re.compile(r"[^\W_]+(?:['’-][^\W_]+)*|[.!?,;:]", re.UNICODE)
DIM=8
MAX_VOCAB=128

def tokenize(text):
    if type(text) is not str or len(text)>40000: raise ValueError('corpus character limit')
    tokens=TOKEN.findall(text.casefold())
    if len(tokens)>5000 or any(len(t)>80 for t in tokens): raise ValueError('token limit')
    return tokens

def digest(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()

def examples(tokens,vocab):
    ids={t:i for i,t in enumerate(vocab)}; seq=[1,1]+[ids.get(t,0) for t in tokens]+[2]
    return [(seq[i-2],seq[i-1],seq[i]) for i in range(2,len(seq))]

class Model:
    def __init__(self,vocab,seed):
        self.vocab=vocab; r=random.Random(seed); n=len(vocab)
        self.e=[[r.uniform(-.2,.2) for _ in range(DIM)] for _ in range(n)]
        self.w=[[r.uniform(-.2,.2) for _ in range(2*DIM)] for _ in range(n)]
        self.b=[0.0]*n
    def probabilities(self,a,b):
        x=self.e[a]+self.e[b]
        logits=[sum(u*v for u,v in zip(row,x))+bias for row,bias in zip(self.w,self.b)]
        peak=max(logits); p=[math.exp(v-peak) for v in logits]; z=sum(p)
        return x,[v/z for v in p]
    def loss(self,rows):
        return sum(-math.log(max(self.probabilities(a,b)[1][y],1e-300)) for a,b,y in rows)/len(rows)
    def step(self,a,b,y,lr):
        x,p=self.probabilities(a,b); p[y]-=1
        # Compute input gradient from old weights before applying SGD.
        dx=[sum(p[i]*self.w[i][j] for i in range(len(p))) for j in range(2*DIM)]
        for i,g in enumerate(p):
            self.b[i]-=lr*g
            for j,v in enumerate(x): self.w[i][j]-=lr*g*v
        for j in range(DIM):
            self.e[a][j]-=lr*dx[j]; self.e[b][j]-=lr*dx[j+DIM]
    def state(self): return {'vocab':self.vocab,'e':self.e,'w':self.w,'b':self.b}
    @classmethod
    def load(cls,state):
        v=state['vocab']; n=len(v)
        if not 3<=n<=MAX_VOCAB or v[:3]!=['<unk>','<bos>','<eos>'] or len(set(v))!=n: raise ValueError('invalid vocabulary')
        for key,width in [('e',DIM),('w',2*DIM)]:
            if len(state[key])!=n or any(len(row)!=width or any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>1000 for x in row) for row in state[key]): raise ValueError('invalid weights')
        if len(state['b'])!=n or any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>1000 for x in state['b']): raise ValueError('invalid bias')
        m=cls(v,0); m.e=state['e']; m.w=state['w']; m.b=state['b']; return m

class Language29:
    def __init__(self,strategy):
        self.s=strategy; self.db=strategy.db
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS language29_corpus(id TEXT PRIMARY KEY, text TEXT, provenance TEXT)')
            self.db.execute('CREATE TABLE IF NOT EXISTS language29_checkpoints(id TEXT PRIMARY KEY, payload TEXT, sha TEXT, report TEXT)')
            self.db.execute('CREATE TABLE IF NOT EXISTS language29_active(slot INTEGER PRIMARY KEY CHECK(slot=1), id TEXT)')
    def add(self,text,source,*,approved=False):
        if approved is not True or type(source) is not str or not 1<=len(source)<=512: raise ValueError('explicit corpus approval and source required')
        tokens=tokenize(text)
        if len(tokens)<3: raise ValueError('corpus too short')
        key=digest(text+'\0'+source)
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO language29_corpus VALUES (?,?,?)',(key,text,source))
            if self.db.execute('SELECT count(*) FROM language29_corpus').fetchone()[0]>32: raise ValueError('corpus capacity')
        return key
    def approve_web(self,key,excerpt,*,approved=False):
        if approved is not True: raise ValueError('explicit review required')
        row=self.db.execute('SELECT record FROM native28_web WHERE id=?',(key,)).fetchone()
        if not row: raise ValueError('snapshot not found')
        rec=json.loads(row[0]); text=rec['text']
        # Reject lossy decoding and records whose raw UTF-8 hash cannot be reproduced.
        if rec.get('id')!=key or digest(text)!=rec.get('sha256') or digest(rec['url']+'\n'+rec['sha256'])!=key: raise ValueError('snapshot integrity mismatch')
        if type(excerpt) is not str or not excerpt or excerpt not in text: raise ValueError('exact excerpt required')
        return self.add(excerpt,'reviewed web snapshot:'+key,approved=True)
    def train(self,seed=29112601,epochs=12):
        if type(seed) is not int or not 0<=seed<2**32 or type(epochs) is not int or not 1<=epochs<=40: raise ValueError('training bounds')
        docs=self.db.execute('SELECT id,text FROM language29_corpus ORDER BY id').fetchall()
        if not docs: raise ValueError('approved corpus required')
        ts=[tokenize(t) for _,t in docs]
        if sum(map(len,ts))>1500: raise ValueError('aggregate training token limit')
        freq=Counter(t for doc in ts for t in doc); v=['<unk>','<bos>','<eos>']+sorted(freq,key=lambda t:(-freq[t],t))[:MAX_VOCAB-3]
        rows=[r for doc in ts for r in examples(doc,v)]
        if len(rows)*epochs*len(v)>1500000: raise ValueError('training operation budget')
        m=Model(v,seed); initial=m.loss(rows); rng=random.Random(seed)
        for _ in range(epochs):
            rng.shuffle(rows)
            for a,b,y in rows: m.step(a,b,y,.075)
        final=m.loss(rows)
        if not math.isfinite(final) or final>=initial: raise ValueError('candidate did not improve training loss')
        payload=json.dumps(m.state(),separators=(',',':'),allow_nan=False); key=digest(payload)
        report={'checkpoint':key,'seed':seed,'epochs':epochs,'examples':len(rows),'vocab':len(v),'initial_loss':initial,'final_loss':final,'corpus_ids':[x[0] for x in docs],'authenticated':False,'provider_attempts':0,'activated':False}
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO language29_checkpoints VALUES (?,?,?,?)',(key,payload,key,json.dumps(report)))
            if self.db.execute('SELECT count(*) FROM language29_checkpoints').fetchone()[0]>16: raise ValueError('checkpoint capacity')
        return report
    def load(self,key=None):
        if key is None:
            row=self.db.execute('SELECT id FROM language29_active WHERE slot=1').fetchone()
            if not row: raise ValueError('no active checkpoint')
            key=row[0]
        row=self.db.execute('SELECT payload,sha FROM language29_checkpoints WHERE id=?',(key,)).fetchone()
        if not row or digest(row[0])!=row[1] or row[1]!=key: raise ValueError('checkpoint integrity mismatch')
        return Model.load(json.loads(row[0]))
    def activate(self,key,*,approved=False):
        if approved is not True: raise ValueError('explicit activation required')
        self.load(key)
        with self.db: self.db.execute('INSERT OR REPLACE INTO language29_active VALUES (1,?)',(key,))
    def generate(self,prompt,max_tokens=12):
        if type(max_tokens) is not int or not 1<=max_tokens<=32: raise ValueError('generation bound')
        m=self.load(); ids={t:i for i,t in enumerate(m.vocab)}; seq=tokenize(prompt)
        context=([1,1]+[ids.get(t,0) for t in seq])[-2:]; out=[]
        for _ in range(max_tokens):
            p=m.probabilities(*context)[1]; y=max(range(2,len(p)),key=lambda i:p[i])
            if y==2: break
            out.append(m.vocab[y]); context=[context[1],y]
        return {'text':' '.join(out),'authenticated':False,'status':'unverified_language_candidate','provider_attempts':0}
    def similar(self,word,limit=5):
        if type(limit) is not int or not 1<=limit<=10: raise ValueError('similarity bound')
        m=self.load(); i=m.vocab.index(word); a=m.e[i]
        def cosine(b):
            den=math.sqrt(sum(x*x for x in a)*sum(x*x for x in b)); return sum(x*y for x,y in zip(a,b))/den if den else 0.0
        rows=sorted([(m.vocab[j],cosine(b)) for j,b in enumerate(m.e) if j>=3 and j!=i],key=lambda r:(-r[1],r[0]))
        return {'neighbors':rows[:limit],'authenticated':False,'status':'learned_distributional_similarity'}
    def converse(self,text):
        if type(text) is not str or len(text)>512: raise ValueError('conversation bound')
        match=re.fullmatch(r'(?i:Does LOGOS support) ([!A-Za-z][A-Za-z0-9_]{0,63})\??',text.strip())
        if match:
            lit=atom(match.group(1)); r=self.s.knowledge.infer(lit,budget=1000,isolate=True)
            return {'text':f'{lit}: {r["status"]} under stored premises.', 'inference':r,'authenticated':False,'provider_attempts':0}
        match=re.fullmatch(r'(?i:calculate) (.{1,256})',text.strip())
        if match: return {'result':self.s.run(match.group(1),native_only=True),'authenticated':False,'provider_attempts':0}
        return {'text':'Unsupported question. Use "Does LOGOS support A?" or "calculate 2+2".','authenticated':False,'status':'abstain','provider_attempts':0}
