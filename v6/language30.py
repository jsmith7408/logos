"""Native bounded attention language prototype; no model providers or pretrained weights."""
import hashlib, json, math, random, re, copy
from collections import Counter
from language29 import tokenize, digest, Language29

CTX=4; DIM=12; HIDDEN=16; MAX_VOCAB=128
SPECIAL=['<unk>','<bos>','<eos>']

def encode_json(x): return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)

def pieces(text, merges):
    out=[]
    for word in tokenize(text):
        if word in merges: out.append('w:'+word)
        else: out.extend('c:'+c for c in '▁'+word)
    return out

def vocabulary(docs):
    freq=Counter(t for d in docs for t in tokenize(d))
    chars=sorted({'c:'+c for w in freq for c in '▁'+w})
    if len(chars)>MAX_VOCAB-3: raise ValueError('training alphabet exceeds vocabulary bound')
    merges=sorted((w for w in freq if freq[w]>=2),key=lambda w:(-freq[w],w))[:min(32,MAX_VOCAB-3-len(chars))]
    return SPECIAL+chars+['w:'+w for w in merges]

def rows(docs,vocab):
    ids={w:i for i,w in enumerate(vocab)}; merges={w[2:] for w in vocab if w.startswith('w:')}; result=[]
    for doc in docs:
        seq=[1]*CTX+[ids.get(w,0) for w in pieces(doc,merges)]+[2]
        result.extend((tuple(seq[i-CTX:i]),seq[i]) for i in range(CTX,len(seq)))
    return result

def softmax(x):
    top=max(x); e=[math.exp(v-top) for v in x]; total=sum(e); return [v/total for v in e]

class AttentionModel:
    def __init__(self,vocab,seed):
        self.vocab=list(vocab); r=random.Random(seed); n=len(vocab)
        def mat(a,b): return [[r.uniform(-.2,.2) for _ in range(b)] for _ in range(a)]
        self.e=mat(n,DIM); self.pos=[0.0]*CTX; self.h=mat(HIDDEN,2*DIM); self.hb=[0.0]*HIDDEN; self.w=mat(n,HIDDEN); self.b=[0.0]*n
    def forward(self,ctx):
        es=[self.e[i] for i in ctx]; q=es[-1]; scale=math.sqrt(DIM)
        a=softmax([sum(x*y for x,y in zip(q,e))/scale+p for e,p in zip(es,self.pos)])
        pooled=[sum(a[i]*es[i][j] for i in range(CTX)) for j in range(DIM)]
        x=pooled+q; h=[math.tanh(sum(u*v for u,v in zip(row,x))+b) for row,b in zip(self.h,self.hb)]
        p=softmax([sum(u*v for u,v in zip(row,h))+b for row,b in zip(self.w,self.b)])
        return es,a,x,h,p
    def loss(self,data):
        if not data: raise ValueError('empty split')
        return sum(-math.log(max(self.forward(ctx)[-1][y],1e-300)) for ctx,y in data)/len(data)
    def step(self,ctx,y,lr):
        es,a,x,h,p=self.forward(ctx); p[y]-=1
        dh=[sum(p[i]*self.w[i][j] for i in range(len(p)))*(1-h[j]*h[j]) for j in range(HIDDEN)]
        dx=[sum(dh[i]*self.h[i][j] for i in range(HIDDEN)) for j in range(2*DIM)]
        da=[sum(dx[j]*e[j] for j in range(DIM)) for e in es]; avg=sum(u*v for u,v in zip(a,da)); ds=[a[i]*(da[i]-avg) for i in range(CTX)]
        scale=math.sqrt(DIM); q=es[-1]; gradients=[[a[i]*dx[j]+ds[i]*q[j]/scale for j in range(DIM)] for i in range(CTX)]
        for j in range(DIM): gradients[-1][j]+=dx[DIM+j]+sum(ds[i]*es[i][j]/scale for i in range(CTX))
        for i,g in enumerate(p):
            self.b[i]-=lr*g
            for j,v in enumerate(h): self.w[i][j]-=lr*g*v
        for i,g in enumerate(dh):
            self.hb[i]-=lr*g
            for j,v in enumerate(x): self.h[i][j]-=lr*g*v
        for i,idx in enumerate(ctx):
            self.pos[i]-=lr*ds[i]
            for j,g in enumerate(gradients[i]): self.e[idx][j]-=lr*g
    def state(self): return copy.deepcopy({k:getattr(self,k) for k in ('vocab','e','pos','h','hb','w','b')})
    @classmethod
    def load(cls,s):
        v=s['vocab']; n=len(v)
        if not 3<=n<=MAX_VOCAB or v[:3]!=SPECIAL or len(set(v))!=n or any(type(t) is not str or len(t)>82 for t in v): raise ValueError('vocabulary')
        def vector(v,n):
            return type(v) is list and len(v)==n and all(type(x) in (float,int) and math.isfinite(x) and abs(x)<=1000 for x in v)
        for key,a,b in [('e',n,DIM),('h',HIDDEN,2*DIM),('w',n,HIDDEN)]:
            if type(s[key]) is not list or len(s[key])!=a or not all(vector(r,b) for r in s[key]): raise ValueError('matrix')
        for key,n0 in [('pos',CTX),('hb',HIDDEN),('b',n)]:
            if not vector(s[key],n0): raise ValueError('vector')
        m=cls(v,0)
        for k in ('e','pos','h','hb','w','b'): setattr(m,k,copy.deepcopy(s[k]))
        return m

class Language30:
    def __init__(self,strategy):
        self.s=strategy; self.db=strategy.db
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS l30_docs(id TEXT PRIMARY KEY, split TEXT, text TEXT, source TEXT, normalized TEXT UNIQUE)')
            self.db.execute('CREATE TABLE IF NOT EXISTS l30_models(id TEXT PRIMARY KEY, payload TEXT, report TEXT)')
            self.db.execute('CREATE TABLE IF NOT EXISTS l30_active(slot INTEGER PRIMARY KEY CHECK(slot=1), id TEXT)')
            self.db.execute('CREATE TABLE IF NOT EXISTS l30_history(seq INTEGER PRIMARY KEY AUTOINCREMENT, previous TEXT, current TEXT, action TEXT)')
    def add(self,text,source,split,*,approved=False):
        if approved is not True or split not in ('train','validation','test') or type(source) is not str or not 1<=len(source)<=512: raise ValueError('explicit approved split and source required')
        t=tokenize(text)
        if len(t)<3: raise ValueError('document too short')
        normalized=digest(' '.join(t)); key=digest(encode_json([text,source,split]))
        with self.db:
            if self.db.execute('SELECT count(*) FROM l30_docs').fetchone()[0]>=24: raise ValueError('document capacity')
            if self.db.execute('SELECT 1 FROM l30_docs WHERE normalized=?',(normalized,)).fetchone(): raise ValueError('duplicate document across splits')
            self.db.execute('INSERT INTO l30_docs VALUES (?,?,?,?,?)',(key,split,text,source,normalized))
        return key
    def review_web(self,key,excerpt,split,*,approved=False):
        # Reuse exact-snapshot integrity check without changing the older corpus.
        if approved is not True: raise ValueError('explicit review required')
        row=self.db.execute('SELECT record FROM native28_web WHERE id=?',(key,)).fetchone()
        if not row: raise ValueError('snapshot not found')
        rec=json.loads(row[0]); text=rec['text']
        if rec.get('id')!=key or digest(text)!=rec.get('sha256') or digest(rec['url']+'\n'+rec['sha256'])!=key: raise ValueError('snapshot integrity mismatch')
        if type(excerpt) is not str or not excerpt or excerpt not in text: raise ValueError('exact excerpt required')
        return self.add(excerpt,'reviewed web snapshot:'+key,split,approved=True)
    def dataset(self):
        docs=self.db.execute('SELECT id,split,text,source,normalized FROM l30_docs ORDER BY id').fetchall()
        groups={k:[] for k in ('train','validation','test')}
        seen=set()
        for key,split,text,source,norm in docs:
            if digest(encode_json([text,source,split]))!=key or digest(' '.join(tokenize(text)))!=norm or norm in seen: raise ValueError('corpus integrity')
            seen.add(norm); groups[split].append(text)
        if not all(groups.values()): raise ValueError('three nonempty splits required')
        v=vocabulary(groups['train']); data={k:rows(d,v) for k,d in groups.items()}
        if sum(map(len,data.values()))>1800: raise ValueError('dataset token budget')
        return digest(encode_json(docs)),v,data
    def active_id(self):
        r=self.db.execute('SELECT id FROM l30_active WHERE slot=1').fetchone(); return r[0] if r else None
    def load(self,key):
        r=self.db.execute('SELECT payload,report FROM l30_models WHERE id=?',(key,)).fetchone()
        if not r or digest(r[0])!=key: raise ValueError('checkpoint integrity')
        payload=json.loads(r[0]); return AttentionModel.load(payload['state']),payload
    def train(self,seed=30112601,epochs=24,patience=4):
        if type(seed) is not int or not 0<=seed<2**32 or type(epochs) is not int or not 1<=epochs<=40 or type(patience) is not int or not 1<=patience<=10: raise ValueError('training bounds')
        split,v,d=self.dataset(); active=self.active_id()
        if len(d['train'])*epochs*len(v)>550000: raise ValueError('training operation bound')
        if active:
            m,old=self.load(active)
            if old['dataset']!=split or m.vocab!=v: raise ValueError('active dataset changed; use separate database for new evaluation protocol')
        else: m=AttentionModel(v,seed)
        initial={k:m.loss(r) for k,r in d.items()}; best=initial['validation']; state=m.state(); best_epoch=0; stale=0; rng=random.Random(seed); curve=[]; tr=list(d['train'])
        for epoch in range(1,epochs+1):
            rng.shuffle(tr)
            for ctx,y in tr: m.step(ctx,y,.045)
            val=m.loss(d['validation']); curve.append({'epoch':epoch,'train':m.loss(tr),'validation':val})
            if val<best-1e-8: best=val; state=m.state(); best_epoch=epoch; stale=0
            else: stale+=1
            if stale>=patience: break
        m=AttentionModel.load(state); final={k:m.loss(r) for k,r in d.items()}
        eligible=best_epoch>0 and final['train']<initial['train'] and final['validation']<initial['validation'] and final['test']<=initial['test'] and all(final[k]<math.inf for k in final)
        payload=encode_json({'state':state,'dataset':split,'baseline':active,'seed':seed,'best_epoch':best_epoch}); key=digest(payload)
        report={'checkpoint':key,'dataset':split,'baseline':active,'seed':seed,'sizes':{k:len(r) for k,r in d.items()},'unknown_targets':{k:sum(y==0 for _,y in r) for k,r in d.items()},'vocab':len(v),'initial':initial,'final':final,'best_epoch':best_epoch,'epochs_run':len(curve),'curve':curve,'eligible':eligible,'authenticated':False,'provider_attempts':0}
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO l30_models VALUES (?,?,?)',(key,payload,encode_json(report)))
            if self.db.execute('SELECT count(*) FROM l30_models').fetchone()[0]>16: raise ValueError('checkpoint capacity')
        return report
    def activate(self,key,*,approved=False):
        if approved is not True: raise ValueError('explicit activation required')
        m,p=self.load(key); split,v,d=self.dataset(); active=self.active_id()
        if p['dataset']!=split or p['baseline']!=active or m.vocab!=v or p['best_epoch']<=0: raise ValueError('stale or invalid candidate')
        baseline=self.load(active)[0] if active else AttentionModel(v,p['seed'])
        before={k:baseline.loss(r) for k,r in d.items()}; after={k:m.loss(r) for k,r in d.items()}
        if not (after['train']<before['train'] and after['validation']<before['validation'] and after['test']<=before['test']): raise ValueError('regression gate failed')
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO l30_active VALUES (1,?)',(key,)); self.db.execute('INSERT INTO l30_history(previous,current,action) VALUES (?,?,?)',(active,key,'activate'))
    def rollback(self,*,approved=False):
        if approved is not True: raise ValueError('explicit rollback required')
        active=self.active_id(); row=self.db.execute("SELECT previous FROM l30_history WHERE current=? AND action='activate' ORDER BY seq DESC LIMIT 1",(active,)).fetchone()
        if not row: raise ValueError('no prior activation')
        prev=row[0]
        if prev: self.load(prev)
        with self.db:
            if prev: self.db.execute('UPDATE l30_active SET id=? WHERE slot=1',(prev,))
            else: self.db.execute('DELETE FROM l30_active')
            self.db.execute('INSERT INTO l30_history(previous,current,action) VALUES (?,?,?)',(active,prev,'rollback'))
        return prev
    def generate(self,prompt,max_tokens=16):
        if type(max_tokens) is not int or not 1<=max_tokens<=32: raise ValueError('generation bound')
        m,_=self.load(self.active_id()); ids={t:i for i,t in enumerate(m.vocab)}; merges={w[2:] for w in m.vocab if w.startswith('w:')}
        ctx=([1]*CTX+[ids.get(t,0) for t in pieces(prompt,merges)])[-CTX:]; out=[]
        for _ in range(max_tokens):
            p=m.forward(ctx)[-1]; y=max(range(2,len(p)),key=lambda i:p[i])
            if y==2: break
            out.append(m.vocab[y]); ctx=ctx[1:]+[y]
        text=''.join((' '+t[2:] if t.startswith('w:') else t[2:].replace('▁',' ')) for t in out).strip()
        return {'text':text,'status':'unverified_language_candidate','authenticated':False,'provider_attempts':0}
    def converse(self,text):
        # Grounded symbolic route only; neural output never supplies premises.
        return Language29(self.s).converse(text)
