"""Offline lexical preflight against measured retail registrations, not a compiler."""
import argparse,collections,hashlib,json,re
from pathlib import Path

SYMBOL_TYPES={'int','flex','float','vector','thing','template','surface','sector','sound','keyframe','model','material','ai','cog','message'}

def scrub(text, literals=True):
    # cog.l recognizes both literal kinds and line comments. It has no C block
    # comment rule. Preserve offsets/newlines so reported source lines stay true.
    token=re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|\#[^\n]*')
    return token.sub(lambda m: m.group() if not literals and m.group()[0] in ('"',"'") else ''.join('\n' if c=='\n' else ' ' for c in m.group()),text)

def inspect(path,target):
    data=path.read_bytes()
    try: text=data.decode('utf-8-sig')
    except UnicodeDecodeError: text=data.decode('cp1252',errors='replace')
    original=text.rstrip('\x1a')
    # Symbols/header lines use the config-file reader before the code lexer.
    # An apostrophe in an unquoted desc=where's value is not a vector opener
    # spanning the later code section. Reset quote handling on each header line.
    declarations_text=''.join(scrub(line,literals=False) for line in original.splitlines(keepends=True))
    ref=Path(__file__).resolve().parents[1]/'references'
    tables={g:json.loads((ref/n).read_text(encoding='utf-8')) for g,n in [('jk','jk101-retail-registry.json'),('mots','mots-retail-registry.json')]}
    verbs={g:{r['name'].lower() for r in rows if r['kind']=='verb'} for g,rows in tables.items()}
    messages={r['name'].lower() for r in tables[target] if r['kind']=='message'}
    float_file=ref/'retail-global-floats.json'
    float_rows=json.loads(float_file.read_text(encoding='utf-8')) if float_file.exists() else []
    float_globals={r['name'].lower() for r in float_rows if r['game']==target and r['kind']=='float'}
    code_start=re.search(r'(?im)^[ \t]*code[ \t\r]*$',declarations_text)
    code_offset=code_start.end() if code_start else 0
    clean=declarations_text[:code_offset]+scrub(original[code_offset:]) if code_start else declarations_text
    code=clean[code_offset:] if code_start else ''
    terminator=re.search(r'\bend\b',code,re.I) # pinned generated lexer folds ASCII case
    if terminator: code=code[:terminator.start()]
    calls=collections.defaultdict(list)
    for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\(',code):
        name=m.group(1).lower()
        if name not in {'if','while','for','switch','return','call'}: calls[name].append(clean.count('\n',0,code_offset+m.start())+1)
    unknown=[{'name':n,'lines':loc,'present_in_other_retail_table':n in verbs['mots' if target=='jk' else 'jk']} for n,loc in sorted(calls.items()) if n not in verbs[target]]
    section=re.search(r'(?ims)^[ \t]*symbols[ \t\r]*$([\s\S]*?)^[ \t]*end[ \t\r]*$',declarations_text)
    declarations=[]; unknown_declarations=[]
    if section:
        for m in re.finditer(r'(?m)^[ \t]*(\w+)[ \t]+([A-Za-z_]\w*)([^\n]*)',section.group(1)):
            kind=m.group(1).lower(); tail=m.group(3).strip()
            d={'type':kind,'semantic_type':'flex' if kind=='float' else kind,'name':m.group(2),'tail':tail,'line':declarations_text.count('\n',0,section.start(1)+m.start())+1}
            if kind=='message':
                alias=re.match(r'\s*=\s*([^\s]+)',tail)
                d['registered_message']=(alias.group(1) if alias else d['name']).lower()
            (declarations if kind in SYMBOL_TYPES else unknown_declarations).append(d)
    declared=[d['registered_message'] for d in declarations if d['type']=='message']
    absent_messages=sorted(set(declared)-messages-float_globals)
    nonstandard_messages=[d for d in declarations if d['type']=='message' and d['registered_message'] in float_globals]
    warnings=[]
    if '/*' in code or '*/' in code: warnings.append('C-style block-comment markers are unsupported by the captured lexer; their contents were not silently removed.')
    if unknown_declarations: warnings.append('Unrecognized declaration types require manual review.')
    if nonstandard_messages: warnings.append('A message binds a measured global float symbol rather than an integer message constant. Generic symbol lookup can accept it; normal event delivery is not established.')
    flags=re.search(r'(?im)^\s*flags\s*=\s*(\S+)',clean)
    return {'file':str(path.resolve()),'sha256':hashlib.sha256(data).hexdigest(),'target':target,'method':'lexical-preflight-v3-not-a-compiler','retail_binary_sha256':tables[target][0]['binary_sha256'],'flags':flags.group(1) if flags else None,'has_symbols':section is not None,'has_code':code_start is not None,'calls':dict(sorted(calls.items())),'calls_absent_from_target_registry':unknown,'declarations':declarations,'unknown_declarations':unknown_declarations,'declared_messages':declared,'messages_absent_from_target_registry':absent_messages,'nonstandard_message_bindings':nonstandard_messages,'literal_resource_references':sorted(set(re.findall(r'(?i)\b[^\s="<>]+\.(?:cog|3do|key|pup|mat|wav|snd|ai)\b',text))),'warnings':warnings,'notes':['Availability is measured for the pinned original executable; it is not an argument/type or runtime check.','Message tables list integer message constants; accepted generic global-symbol aliases and actual event delivery are separate questions.','Resource spellings are a discovery heuristic and may include comments; dynamic references are not resolved.','Changing the source can affect bytecode layout; this tool does not predict multiplayer checksums.'],'availability_findings':len(unknown)+len(absent_messages)}

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('cog',type=Path); ap.add_argument('--target',choices=['jk','mots'],required=True); ap.add_argument('--strict',action='store_true',help='Exit 2 on unavailable call/message spellings'); args=ap.parse_args()
    result=inspect(args.cog,args.target); print(json.dumps(result,indent=2,ensure_ascii=False))
    if args.strict and result['availability_findings']: raise SystemExit(2)
if __name__=='__main__': main()
