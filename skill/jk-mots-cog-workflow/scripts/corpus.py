#!/usr/bin/env python3
"""Offline metadata/notes lookup, with an optional user-owned source corpus."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import runpy
import sys

SKILL = Path(__file__).resolve().parents[1]

def rows(path):
    if not path.exists(): return
    with path.open(encoding='utf-8-sig') as f:
        for line in f:
            if line.strip(): yield json.loads(line)

def main():
    argv = sys.argv[1:]
    root = Path(os.environ.get('COG_CORPUS_ROOT', str(SKILL/'data'))).expanduser()
    if '--root' in argv:
        pos = argv.index('--root')
        if pos+1 >= len(argv): raise SystemExit('--root requires a path')
        root = Path(argv[pos+1]).expanduser()
        del argv[pos:pos+2]
    root = root.resolve()
    delegate = root/'scripts'/'corpus_index.py'
    if delegate.is_file() and argv and argv[0] in ('stats','search','show'):
        # An explicit local override selects a user-controlled local tool.
        # No build, acquisition or publication operation is forwarded.
        sys.path.insert(0,str(delegate.parent))
        sys.argv=[str(delegate),'--root',str(root),*argv]
        runpy.run_path(str(delegate),run_name='__main__')
        return
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('stats')
    s=sub.add_parser('search'); s.add_argument('query'); s.add_argument('--kind',choices=['cog','source','note','all'],default='all'); s.add_argument('--game',choices=['jk','mots']); s.add_argument('--limit',type=int,default=20)
    h=sub.add_parser('show'); h.add_argument('identity'); h.add_argument('--source',action='store_true')
    a=p.parse_args(argv)
    if not (root/'catalog').is_dir(): p.error('No corpus catalog at selected root; use --root to select public or locally imported corpus.')
    if a.command=='stats':
        print((root/'stats.json').read_text(encoding='utf-8')); return
    if a.command=='show':
        if a.source and not (root/'PRIVATE_LOCAL_CORPUS').is_file(): p.error('Raw source is not distributed; --source requires an explicitly imported private corpus.')
        for name in ('cogs','sources'):
            for row in rows(root/'catalog'/f'{name}.jsonl'):
                if a.identity in (row.get('sha256'),row.get('id')):
                    if a.source:
                        rel=row.get('object_path')
                        if not rel: p.error('This record contains metadata only.')
                        obj=(root/rel).resolve()
                        if root not in obj.parents: p.error('Object path escapes corpus root.')
                        data=obj.read_bytes()
                        import hashlib
                        if hashlib.sha256(data).hexdigest()!=row['sha256']: p.error('Object hash mismatch.')
                        try: print(data.decode('utf-8-sig'))
                        except UnicodeDecodeError: print(data.decode('cp1252',errors='replace'))
                    else: print(json.dumps(row,indent=2,ensure_ascii=False))
                    return
        p.error('Identity not found; use the full SHA-256 or source ID.')
    if not 1 <= a.limit <= 1000: p.error('--limit must be between 1 and 1000')
    query=a.query.casefold(); found=0
    for kind,file in [('cog','cogs'),('source','sources')]:
        if a.kind not in (kind,'all'): continue
        for row in rows(root/'catalog'/f'{file}.jsonl'):
            games=row.get('games',[row.get('game')])
            if a.game and a.game not in games: continue
            if query not in json.dumps(row,ensure_ascii=False).casefold(): continue
            if kind=='cog':
                result={k:row[k] for k in ('sha256','bytes','names','games','calls','messages','tags') if k in row}
                result['provenance']=row.get('provenance',[])[:5]
            else: result=row
            print(json.dumps({'kind':kind,**result},ensure_ascii=False)); found+=1
            if found>=a.limit:return
    if a.kind in ('note','all'):
        notes=root/'notes' if (root/'notes').is_dir() else SKILL/'references'
        for path in sorted(notes.glob('*.md')):
            for num,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
                if query in line.casefold():
                    print(json.dumps({'kind':'note','name':path.name,'line':num,'text':line},ensure_ascii=False));found+=1
                    if found>=a.limit:return
    if not found: print(json.dumps({'matches':0,'query':a.query}))

if __name__=='__main__':main()
