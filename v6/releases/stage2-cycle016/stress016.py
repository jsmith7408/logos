import random,time,sys
from stage2_causal import causal
seed=int(sys.argv[1]); duration=float(sys.argv[2]); r=random.Random(seed); start=time.monotonic(); n=0
while time.monotonic()-start<duration:
    a,b,c=[bool(r.getrandbits(1)) for _ in range(3)]
    m=[{'name':'A','parents':[],'table':[a]},{'name':'B','parents':['A'],'table':[b,not b]},{'name':'C','parents':['A','B'],'table':[c,not c,not c,c]}]
    override={k:bool(r.getrandbits(1)) for k in 'AB' if r.getrandbits(1)}
    x=override.get('A',a); y=override.get('B',b^x)
    result=causal(m,override,'C')
    assert result['factual']==(c^a^(b^a)) and result['counterfactual']==(c^x^y)
    n+=1
print(f'seed={seed} cases={n} seconds={time.monotonic()-start:.3f}')
