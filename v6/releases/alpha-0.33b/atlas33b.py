"""Local Atlas retrieval; imported text is never authenticated evidence."""
import argparse, hashlib, json, sqlite3, zipfile, re
from contextlib import closing
PREFIX='LOGOS_Research_Atlas/'
def ingest(db, archive):
    with zipfile.ZipFile(archive) as z:
        for name in ('sources.json','records.jsonl'):
            if z.getinfo(PREFIX+name).file_size>64*1024*1024: raise ValueError('size limit')
        source_raw=z.read(PREFIX+'sources.json'); sources=json.loads(source_raw)
        raw=z.read(PREFIX+'records.jsonl'); digest=hashlib.sha256(b'LOGOS-atlas-v2\0'+hashlib.sha256(raw).digest()+hashlib.sha256(source_raw).digest()).hexdigest()
        rows=[]
        for i,line in enumerate(raw.splitlines()):
            r=json.loads(line); s=r['s']
            if type(s) is not int or not 0<=s<len(sources): raise ValueError('source index')
            src=sources[s]
            rows.append((digest,i,src['name'],src['sha256'],src['genre'],r['loc'],r['text'],json.dumps(r['tags'])))
    with closing(sqlite3.connect(db)) as c,c:
        c.execute('CREATE TABLE IF NOT EXISTS atlas_imports(digest TEXT PRIMARY KEY, source_manifest TEXT NOT NULL)')
        c.execute('CREATE VIRTUAL TABLE IF NOT EXISTS atlas USING fts5(digest UNINDEXED, record_id UNINDEXED, source UNINDEXED, source_hash UNINDEXED, genre UNINDEXED, location UNINDEXED, passage, tags)')
        c.execute('BEGIN IMMEDIATE')
        if c.execute('SELECT 1 FROM atlas_imports WHERE digest=?',(digest,)).fetchone(): return {'inserted':0,'digest':digest}
        c.executemany('INSERT INTO atlas VALUES(?,?,?,?,?,?,?,?)',rows)
        c.execute('INSERT INTO atlas_imports VALUES(?,?)',(digest,json.dumps(sources)))
    return {'inserted':len(rows),'digest':digest}
def search(db, query, limit=10):
    if type(limit) is not int or not 1<=limit<=50: raise ValueError('limit')
    tokens=re.findall(r'\w+',query[:500])[:20]
    if not tokens: return []
    expression=' AND '.join('"'+t+'"' for t in tokens)
    with closing(sqlite3.connect(db)) as c:
        c.row_factory=sqlite3.Row
        rows=c.execute('SELECT *, bm25(atlas) AS rank FROM atlas WHERE atlas MATCH ? ORDER BY rank, digest, record_id LIMIT ?',(expression,limit)).fetchall()
        return [dict(r,status='unverified',source_hash_status='reported_not_verified') for r in rows]
def main():
    p=argparse.ArgumentParser(); p.add_argument('--db',required=True); s=p.add_subparsers(dest='cmd',required=True); s.add_parser('ingest').add_argument('archive'); q=s.add_parser('search'); q.add_argument('query'); q.add_argument('--limit',type=int,default=10); a=p.parse_args(); print(json.dumps(ingest(a.db,a.archive) if a.cmd=='ingest' else search(a.db,a.query,a.limit),ensure_ascii=False))
if __name__=='__main__': main()
