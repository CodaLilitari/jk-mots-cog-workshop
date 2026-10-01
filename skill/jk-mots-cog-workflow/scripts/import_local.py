#!/usr/bin/env python3
"""Passively import explicit owned/authorized COG, GOB, GOO and ZIP inputs locally.

No network, no installers, no code execution, no source modification. Output is
marked PRIVATE_LOCAL_CORPUS and is never included by the public exporter.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import struct
import tempfile
import zipfile
from inspect_cog import inspect

EXT={'.cog','.gob','.goo','.zip'}
MAX_MEMBER=512*1024*1024
MAX_COG=8*1024*1024
MAX_MEMBERS=200000
MAX_EXPANSION=4*1024*1024*1024
MAX_DEPTH=4
MAX_INPUT_FILES=4096
MAX_DISCOVERY_ENTRIES=50000
MAX_TOTAL_MEMBERS=50000
MAX_COG_OCCURRENCES=20000
MAX_UNIQUE_COGS=8192
SPOOL_BYTES=8*1024*1024

class ImportLimit(ValueError):
    """Stop the import immediately when a global workload limit is reached."""

def outside_checkout(path):
    path=Path(path).expanduser().absolute()
    for candidate in (path,path.resolve()):
        for ancestor in (candidate,*candidate.parents):
            if (ancestor/'.git').exists():
                raise ValueError('Private corpus output must be outside Git checkouts; choose a separate --out directory.')
    return path.resolve()

def is_link(path):
    return path.is_symlink() or bool(getattr(path.lstat(),'st_file_attributes',0)&0x400)

def discover_inputs(inputs,out):
    files=set();pending=[];visited=0
    for item in inputs:
        item=item.expanduser().absolute()
        if is_link(item):raise ValueError('Input roots cannot be symlinks or junctions.')
        item=item.resolve()
        if item==out or out in item.parents or item in out.parents:
            raise ValueError('Input and output directories must not contain each other.')
        if item.is_dir():pending.append(item)
        elif item.is_file() and item.suffix.lower() in EXT:files.add(item)
        else:raise ValueError('Input is absent or unsupported: '+str(item))
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                visited+=1
                if visited>MAX_DISCOVERY_ENTRIES:raise ImportLimit('Input discovery limit exceeded; select smaller explicit folders.')
                path=Path(entry.path)
                if entry.name=='.git' or is_link(path):continue
                if entry.is_dir(follow_symlinks=False):pending.append(path)
                elif entry.is_file(follow_symlinks=False) and path.suffix.lower() in EXT:files.add(path)
                if len(files)>MAX_INPUT_FILES:raise ImportLimit('Input file limit exceeded; import smaller batches.')
    if len(files)>MAX_INPUT_FILES:raise ImportLimit('Input file limit exceeded; import smaller batches.')
    return files

def digest(data):return hashlib.sha256(data).hexdigest()
def file_digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def safe_name(name):
    name=name.replace('\\','/')
    if not name or name.startswith('/') or ':' in name or '\0' in name or '..' in PurePosixPath(name).parts:raise ValueError('Unsafe archive member path')
    return name
def write_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def write_rows(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8') as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False)+'\n')

class Importer:
    def __init__(self,out,game):
        self.out=outside_checkout(out);self.game=game;self.cogs={};self.sources=[];self.errors=[];self.expanded=0;self.archives=0;self.members=0;self.occurrences=0
    def visit(self,count):
        self.members+=count
        if self.members>MAX_TOTAL_MEMBERS:raise ImportLimit('Total member limit exceeded; import smaller batches.')
    def account(self,size):
        if size<0 or size>MAX_MEMBER:raise ValueError('Member byte limit exceeded')
        self.expanded+=size
        if self.expanded>MAX_EXPANSION:raise ImportLimit('Total expansion limit exceeded')
    def import_member(self,source,size,member,chain,depth,details):
        self.account(size)
        if Path(member).suffix.lower()=='.cog' and size>MAX_COG:raise ValueError('COG byte limit exceeded')
        # Nested containers spill to temporary disk instead of accumulating in RAM.
        with tempfile.SpooledTemporaryFile(max_size=SPOOL_BYTES,mode='w+b') as temp:
            h=hashlib.sha256();remaining=size
            while remaining:
                chunk=source.read(min(65536,remaining))
                if not chunk:raise ValueError('Short archive member read')
                h.update(chunk);temp.write(chunk);remaining-=len(chunk)
            child={'name':member,'bytes':size,'sha256':h.hexdigest(),'container_sha256':chain[-1]['sha256'],**details}
            temp.seek(0);self.walk(temp,size,member,[*chain,child],depth+1)
    def cog(self,data,name,chain):
        if len(data)>MAX_COG:raise ValueError('COG byte limit exceeded')
        h=digest(data); rel='objects/'+h[:2]+'/'+h+'.cog';obj=self.out/rel
        self.occurrences+=1
        if self.occurrences>MAX_COG_OCCURRENCES:raise ImportLimit('COG occurrence limit exceeded; import smaller batches.')
        if h not in self.cogs and len(self.cogs)>=MAX_UNIQUE_COGS:raise ImportLimit('Distinct COG limit exceeded; import smaller batches.')
        obj.parent.mkdir(parents=True,exist_ok=True)
        if obj.exists():
            if file_digest(obj)!=h:raise ValueError('Existing immutable object has wrong hash')
        else:obj.write_bytes(data)
        if h not in self.cogs:
            a=inspect(obj,self.game)
            self.cogs[h]={'sha256':h,'bytes':len(data),'names':[],'games':[self.game],'calls':{k:len(v) for k,v in a['calls'].items()},'messages':sorted(set(a['declared_messages'])),'tags':[], 'provenance':[],'object_path':rel,'analysis_method':a['method']}
        row=self.cogs[h]
        if name not in row['names']:row['names'].append(name)
        row['provenance'].append({'source_id':chain[0]['sha256'],'member':name,'game':self.game,'chain':chain,'basis':'Explicit user-provided local input; original bytes retained. Target label is user-selected, not a compatibility verdict.'})
    def walk(self,f,size,name,chain,depth):
        if depth>MAX_DEPTH:raise ValueError('Archive depth limit exceeded')
        ext=Path(name).suffix.lower()
        if ext=='.cog':
            if size>MAX_COG:raise ValueError('COG byte limit exceeded')
            f.seek(0);self.cog(f.read(),name,chain);return
        self.archives+=1
        if ext in ('.gob','.goo'):
            if size<16:raise ValueError('Truncated GOB header')
            f.seek(0);magic,version,offset=struct.unpack('<4sII',f.read(12))
            if magic!=b'GOB ' or version!=20:raise ValueError('Unsupported GOB signature/version')
            if offset<12 or offset+4>size:raise ValueError('GOB directory outside file')
            f.seek(offset);count=struct.unpack('<I',f.read(4))[0];end=offset+4+136*count
            if count>MAX_MEMBERS or end>size:raise ValueError('GOB directory bounds/count invalid')
            self.visit(count)
            entries=[]
            for ordinal in range(count):
                start,length,raw=struct.unpack('<Ii128s',f.read(136))
                if b'\0' not in raw:raise ValueError('GOB member name not terminated')
                member=safe_name(raw.split(b'\0',1)[0].decode('cp1252',errors='replace'))
                if length<0 or start<12 or start+length>size or (length and start<end and start+length>offset):raise ValueError('GOB member extent invalid/overlaps directory')
                entries.append((ordinal,start,length,member))
            for ordinal,start,length,member in entries:
                if Path(member).suffix.lower() not in EXT:continue
                try:
                    f.seek(start);self.import_member(f,length,member,chain,depth,{'ordinal':ordinal,'offset':start})
                except ImportLimit:raise
                except (ValueError,zipfile.BadZipFile,RuntimeError,OSError) as e:self.errors.append({'container_sha256':chain[-1]['sha256'],'member':member,'error':str(e)})
        elif ext=='.zip':
            with zipfile.ZipFile(f) as z:
                infos=z.infolist()
                if len(infos)>MAX_MEMBERS:raise ValueError('ZIP member count limit exceeded')
                self.visit(len(infos))
                for ordinal,item in enumerate(infos):
                    if item.is_dir():continue
                    member=safe_name(item.filename)
                    if Path(member).suffix.lower() not in EXT:continue
                    try:
                        if item.flag_bits&1:raise ValueError('Encrypted ZIP member; not imported')
                        if item.file_size/max(item.compress_size,1)>1000:raise ValueError('ZIP expansion ratio limit exceeded')
                        with z.open(item) as member_stream:
                            self.import_member(member_stream,item.file_size,member,chain,depth,{'ordinal':ordinal,'crc32':f'{item.CRC:08x}'})
                    except ImportLimit:raise
                    except (ValueError,zipfile.BadZipFile,RuntimeError,OSError,NotImplementedError) as e:self.errors.append({'container_sha256':chain[-1]['sha256'],'member':member,'error':str(e)})

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game',choices=['jk','mots'],required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('inputs',nargs='+',type=Path);a=p.parse_args()
    try:out=outside_checkout(a.out)
    except ValueError as e:p.error(str(e))
    if out.exists() and any(out.iterdir()):p.error('Choose a new empty private output directory; existing corpora are not overwritten.')
    try:files=discover_inputs(a.inputs,out)
    except (ValueError,OSError) as e:p.error(str(e))
    if not files:p.error('No supported inputs found.')
    out.mkdir(parents=True,exist_ok=True);(out/'PRIVATE_LOCAL_CORPUS').write_text('Contains owned or authorized source material. Do not publish by default.\n',encoding='utf-8');(out/'.gitignore').write_text('*\n',encoding='utf-8')
    importer=Importer(out,a.game)
    for path in sorted(files):
        try:
            h=file_digest(path);size=path.stat().st_size
            chain=[{'name':path.name,'sha256':h,'bytes':size,'input_path':str(path)}]
            importer.sources.append({'id':h,'sha256':h,'bytes':size,'filename':path.name,'game':a.game,'local_path':str(path),'rights':'Local input only; no redistribution license inferred.'})
            with path.open('rb') as f:importer.walk(f,size,path.name,chain,0)
        except ImportLimit as e:
            importer.errors.append({'input_path':str(path),'error':str(e),'stopped':True});break
        except (ValueError,zipfile.BadZipFile,RuntimeError,OSError) as e:importer.errors.append({'input_path':str(path),'error':str(e)})
    write_rows(out/'catalog'/'cogs.jsonl',sorted(importer.cogs.values(),key=lambda r:r['sha256']));write_rows(out/'catalog'/'sources.jsonl',importer.sources)
    stats={'schema':1,'private':True,'game_label':a.game,'input_files':len(importer.sources),'archives_read':importer.archives,'distinct_cog_bodies':len(importer.cogs),'cog_occurrences':sum(len(r['provenance']) for r in importer.cogs.values()),'errors':len(importer.errors),'limits':{'member_bytes':MAX_MEMBER,'cog_bytes':MAX_COG,'expanded_bytes':MAX_EXPANSION,'depth':MAX_DEPTH,'input_files':MAX_INPUT_FILES,'discovery_entries':MAX_DISCOVERY_ENTRIES,'total_members':MAX_TOTAL_MEMBERS,'cog_occurrences':MAX_COG_OCCURRENCES,'distinct_cogs':MAX_UNIQUE_COGS,'spool_bytes':SPOOL_BYTES},'method':'Passive extraction, member bounds and exact hashes. No source execution or runtime compatibility validation.'}
    write_json(out/'stats.json',stats);write_json(out/'import-errors.json',importer.errors);print(json.dumps(stats,indent=2))
    if importer.errors:raise SystemExit(2)

if __name__=='__main__':main()
