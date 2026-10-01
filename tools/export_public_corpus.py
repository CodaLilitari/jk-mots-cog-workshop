#!/usr/bin/env python3
"""Build a field-allowlisted public metadata corpus from an authorized local corpus.

No networking. No raw scripts, messages, captures, third-party manuals or binaries
are copied. Reviewed authored notes are pinned by hash, not auto-approved by a
redaction regex. Changing an input note requires a fresh publication review.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl, unquote

PIN = 'b1be98bd4f170b5384cb71b15443a274aac6a937'
SOURCE_BASE = 'https://github.com/CodaLilitari/OpenJKDF2-MotS-Fixes/blob/' + PIN + '/'
REVIEWED_NOTES = {
    'language-and-execution.md': '90d2d2a78cdc8a10d34cd0ddeb4c5614485d86f52f80bcd08607cddb636ae585',
    'authoring-and-testing.md': 'a01a4154c61f807460581be1617b59567ae7091be51721fbec6f3d361c02fa65',
    'authoring-decisions.md': 'be8759f3503a1c2450cf36e81cde38da978fd5846a3df2efd74667370dfd9e6f',
    'checksums-and-retail.md': '5c51dd3c33a5bce960c9e877b9aaf81dbc512f0b80f7ab6c5892959e1a804a7e',
    'engine-findings.md': 'a056fdab701c1040d890ffceb1660c5559f009e129fdf9cdddfb6d7685cab3f4',
    'verb-families.md': 'de320c8e7c5b24d40f8ef3452619c91ed4dc28b7e489b590212466700841e481',
    'pattern-atlas.md': 'b3b152bfc042a06953d243f41a3ff35876536e5e8fc587a0fc70cbab50c2e1db',
    'beefcaike-cog-study.md': '9de6f03dc931bfa4117037dbc4b9e9b4497f8dc6cbc8e694600ea4c4949ee065',
    'triscuit-generator-engine.md': 'cd25ba758524c187d1edde62f5b2b34568ff1e518f01738f3487b1a2baf25a49',
}
PUBLIC_AUTHORED_NOTES = ('case-lessons.md', 'historical-sources.md', 'research-and-retrieval.md')
# Each lane was reviewed as a public source collection; nested free text, body,
# capture, origins, local paths, credentials and discovery context are omitted.
MANIFESTS = {
    'massassi-packages/sources.jsonl': 'massassi-packages',
    'forums/sources.jsonl': 'massassi-cog-forum',
    'editing-forums/sources.jsonl': 'massassi-editing-forum',
    'documentation/sources.jsonl': 'public-documentation',
    'supplemental/sources.jsonl': 'public-supplemental',
    'external-community/jkarchive-payloads.jsonl': 'jkarchive-packages',
    'external-community/payloads.jsonl': 'tacc-packages',
    'external-community/tool-payloads.jsonl': 'jkarchive-cog-tools',
    'external-sites/sources.jsonl': 'public-author-sites',
    'reference-sites/sources.jsonl': 'public-reference-sites',
}
HOSTS = {
    'www.massassi.net', 'massassi.net', 'forums.massassi.net', 'www.massassi.com', 'massassi.com',
    'tacc.massassi.net', 'jkdf2.net', 'www.jkdf2.net', 'www.dralloc.net', 'dralloc.net',
    '420union.atspace.com', 'sithmercenaries.net', 'www.sithmercenaries.net',
    'sithmercenaries.com', 'www.sithmercenaries.com', 'www.jkhub.net', 'jkhub.net',
    'www.commandchamber.net', 'commandchamber.net', 'edward.leuf.org',
    'www.jediknight.net', 'jediknight.net', 'gamebanana.com', 'api.gamebanana.com',
    'www.jkhub.org', 'jkhub.org', 'www.moddb.com', 'moddb.com',
    'jkdf2.com', 'www.jkdf2.com', 'jkdf2.net', 'millennium.massassi.net',
    'web.archive.org', 'www.geocities.com', 'geocities.com', 'eah-triscuit.com',
    'www.eah-triscuit.com', 'www.angelfire.com', 'angelfire.com',
    'www.jediknightdf2.com', 'jediknightdf2.com', 'jkhub.net',
}
QUERY_KEYS = {'id', 'fid', 'dir', 'page', 'itemtype', 'itemid', 'fields', 'return_keys'}
HASH = re.compile(r'^[0-9a-f]{64}$')
IDENTIFIER = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
PRIVATE_PATTERN = re.compile(r'(?:[A-Za-z]:[\\/](?:Users|Program Files)|/(?:home|Users)/|discord(?:app)?\.(?:com|net)/|cdn\.discord|media\.discord|[?&](?:token|signature|sig|ex|is|hm|key|auth)=)', re.I)

def sha(data): return hashlib.sha256(data).hexdigest()
def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def jsonl(path):
    with path.open(encoding='utf-8-sig') as f:
        for line in f:
            if line.strip(): yield json.loads(line)
def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as f:
        for row in rows: f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')
def safe_text(value, limit=400):
    if not isinstance(value, str) or PRIVATE_PATTERN.search(value): return None
    if any(ord(c) < 32 for c in value): return None
    if len(value) > limit: return None
    return value.strip() or None
def safe_url(value):
    if not isinstance(value, str) or PRIVATE_PATTERN.search(unquote(value)): return None
    u = urlsplit(value)
    if u.scheme not in ('http', 'https') or u.username or u.password or u.fragment: return None
    if u.hostname not in HOSTS: return None
    if any(k.lower() not in QUERY_KEYS for k, _ in parse_qsl(u.query)): return None
    if u.hostname == 'web.archive.org':
        m = re.match(r'^/web/[0-9]{4,14}(?:id_|im_)?/(https?://.+)$', u.path)
        if not m or not safe_url(m.group(1)): return None
    return value
def member_name(value):
    if not isinstance(value, str): return None
    value = value.replace('\\', '/')
    if value.startswith('/') or ':' in value or '..' in value.split('/'): return None
    return safe_text(value, 250)
def game_of(row):
    game = row.get('game')
    if game in ('jk', 'mots'): return game
    cat = str(row.get('category', '')).lower()
    if cat.startswith('jk'): return 'jk'
    if cat.startswith(('mots', 'mot')): return 'mots'
    return 'unresolved'

def source_record(row, collection):
    url = safe_url(row.get('url') or row.get('request_url'))
    if not url: return None
    record = {'id': 'src-' + sha(url.encode())[:24], 'collection': collection, 'url': url}
    for field in ('title', 'author', 'category', 'filename'):
        val = safe_text(row.get(field))
        if val: record[field] = val
    page = safe_url(row.get('page_url'))
    if page: record['page_url'] = page
    value = row.get('sha256')
    if isinstance(value, str) and HASH.fullmatch(value): record['sha256'] = value
    value = row.get('bytes')
    if isinstance(value, int) and value >= 0: record['bytes'] = value
    value = row.get('status') if isinstance(row.get('status'), int) else row.get('http_status')
    if isinstance(value, int): record['observed_status'] = value
    value = safe_text(row.get('status'), 50)
    if value: record['retrieval_state'] = value
    final = safe_url(row.get('final_url'))
    if final and final != url: record['final_url'] = final
    value = safe_text(row.get('content_type'), 120)
    if value: record['content_type'] = value
    record['identity_scope'] = 'Recorded retrieval bytes; a hash or HTTP 200 alone does not establish a valid package.'
    record['game'] = game_of(row)
    record['rights'] = 'Original author rights retained; metadata record is not redistribution permission.'
    return record

def adapt_note(name, raw):
    """Transform only the exact manually reviewed authored document version."""
    if sha(raw) != REVIEWED_NOTES[name]:
        raise ValueError('Authored note changed; fresh publication review required: ' + name)
    text = raw.decode('utf-8-sig')
    # Preserve authored analysis. Public source code anchors point at exact commit;
    # local evidence is deliberately not presented as a publicly linked artifact.
    def link(m):
        label, target = m.group(1), m.group(2).strip('<>')
        if '/engine/source_snapshot/' in target:
            tail = target.split('/engine/source_snapshot/', 1)[1]
            tail = re.sub(r':(\d+)$', r'#L\1', tail)
            return '[' + label + '](' + SOURCE_BASE + tail + ')'
        if re.match(r'^[A-Za-z]:[\\/]', target):
            return label + ' (retained local evidence)'
        if target in ('custom-script-cases.md', 'historical-archives.md', 'recovered-integration-cases.md'):
            return '[' + label + '](case-lessons.md)'
        return m.group(0)
    text = re.sub(r'\[([^\]]+)\]\((<[^>]+>|[^)]+)\)', link, text)
    text = re.sub(r'^\[[A-Z][0-9]+\]: <[A-Za-z]:[^\n]+\n?', '', text, flags=re.M)
    text = text.replace('Each ID links to immutable local source bytes.', 'Each ID identifies an exact retail source hash; source bytes are intentionally excluded.')
    text = text.replace('The source IDs below resolve to full hashes, local immutable objects, archive/member provenance, and handler entry lines in the registry at the end. `local/pattern-atlas-sources.json` is the machine-readable companion. `pattern-atlas-diff-spans.json` records literal changed line spans for the four direct JK/MotS pairs. Author initials are reproduced as present in the headers; this atlas does not expand them speculatively.', 'The source IDs below identify full hashes, member filenames and handler entry lines in the registry at the end. The public metadata catalog supplies approved source associations; original objects, detailed member chains and literal comparison spans remain local evidence and are not distributed. Author initials are reproduced as present in the headers; this atlas does not expand them speculatively.')
    text = text.replace('Full ISO/archive/member chains and handler line numbers are in `local/pattern-atlas-sources.json`.', 'Full ISO/archive/member chains remain retained local evidence; the public registry below preserves the exact member hashes and handler line numbers.')
    text = text.replace('stops at the first lowercase `end` token', 'stops at the first case-folded `end` token')
    text = text.replace("`timer` is passed as the verb's speed argument.", "`timer` is passed as the verb's duration argument in the pinned implementation.")
    # One integration anecdote names a private attachment; retain only the
    # publicly inspectable implementation contract in this public edition.
    text = re.sub(r' The Gunrunner skill-selection review \(retained local evidence\) shows both uses:.*? This is a pinned-source contract, not fresh original-retail execution\.', ' This is a pinned-source contract, not fresh original-retail execution.', text)
    # No private evidence files are promised in the public package.
    preface = ('> Public research edition. This is original authored analysis, not a source-code dump. '
        'References marked "retained local evidence" were inspected during research but their raw artifacts '
        'are not distributed. Binary identities, measured registries and public package identities are '
        'included; source execution and retail gameplay remain different evidence grades.\n\n')
    pos = text.find('\n')
    text = text[:pos+1] + '\n' + preface + text[pos+1:].lstrip('\n')
    if PRIVATE_PATTERN.search(text): raise ValueError('Private marker remains in note ' + name)
    return text

def build(root, source_skill, dest):
    corpus = dest/'corpus'
    skill = dest/'skill'/'jk-mots-cog-workflow'
    audit = {'schema': 1, 'policy': 'Explicit source-lane, field, host, note-version and output allowlists; no raw payload redistribution.', 'inputs': [], 'note_reviews': [], 'omissions': {}, 'output_files': []}
    sources = {}
    for rel, collection in MANIFESTS.items():
        path = root/rel
        if not path.is_file(): continue
        data = path.read_bytes()
        audit['inputs'].append({'label': rel, 'sha256': sha(data), 'kind': 'public-source-metadata-input'})
        for row in jsonl(path):
            record = source_record(row, collection)
            if record: sources[record['url']] = record
    # Public GameBanana author payloads have acquisition metadata nested one level.
    path = root/'gamebanana'/'author-payloads.json'
    if path.is_file():
        audit['inputs'].append({'label': 'gamebanana/author-payloads.json', 'sha256': sha(path.read_bytes()), 'kind': 'public-source-metadata-input'})
        for item in json.loads(path.read_text(encoding='utf-8')):
            row = dict(item.get('acquisition', {}))
            row.update(filename=item.get('filename'), game='jk', page_url='https://gamebanana.com/mods/' + str(item['mod_id']))
            record = source_record(row, 'gamebanana-public-packages')
            if record: sources[record['url']] = record
    # Archived author pages: preserve original and actual retrieval URL as facts.
    path = root/'historical'/'retrievals.jsonl'
    if path.is_file():
        audit['inputs'].append({'label': 'historical/retrievals.jsonl', 'sha256': sha(path.read_bytes()), 'kind': 'public-author-archive-metadata-input'})
        for row in jsonl(path):
            record = source_record(row, 'historical-public-archives')
            if record:
                original = safe_url(row.get('original_url'))
                if original: record['original_url'] = original
                sources[record['url']] = record
    source_rows = sorted(sources.values(), key=lambda r: r['url'])
    write_jsonl(corpus/'catalog'/'sources.jsonl', source_rows)
    url_to_source = {r['url']: r['id'] for r in source_rows}
    for r in source_rows:
        if r.get('original_url'): url_to_source[r['original_url']] = r['id']
    cog_rows = []
    omitted = 0
    path = root/'analysis'/'profiles.jsonl'
    audit['inputs'].append({'label': 'analysis/profiles.jsonl', 'sha256': sha(path.read_bytes()), 'kind': 'field-filtered-local-profile-input'})
    for profile in jsonl(path):
        if not isinstance(profile.get('sha256'), str) or not HASH.fullmatch(profile['sha256']):
            raise ValueError('Malformed source profile SHA-256')
        if not isinstance(profile.get('bytes'), int) or profile['bytes'] < 0:
            raise ValueError('Malformed source profile size')
        provenance = []
        for occurrence in profile.get('occurrences', []):
            member = member_name(occurrence.get('name'))
            if not member: continue
            game = occurrence.get('game') if occurrence.get('game') in ('jk', 'mots') else 'unresolved'
            classification = occurrence.get('classification')
            if classification in ('retail-jk', 'retail-mots'):
                provenance.append({'source_id': 'owned-retail-' + game, 'member': member, 'game': game, 'basis': 'Observed owned retail provenance; not a runtime compatibility claim.'})
            else:
                # A public source identity is required. No private occurrence is
                # retained simply because another occurrence has the same hash.
                source = url_to_source.get(occurrence.get('source_url'))
                if source: provenance.append({'source_id': source, 'member': member, 'game': game, 'basis': 'Public source package/page association; game label is catalog provenance.'})
        if not provenance:
            omitted += 1
            continue
        provenance = [json.loads(s) for s in sorted({json.dumps(p, sort_keys=True) for p in provenance})]
        analysis = profile.get('analysis', {})
        calls = {k: v for k, v in analysis.get('calls', {}).items() if IDENTIFIER.fullmatch(k) and len(k) <= 80 and isinstance(v, int)}
        messages = sorted(n for n in analysis.get('messages', []) if IDENTIFIER.fullmatch(n) and len(n) <= 80)
        tags = [t for t in analysis.get('heuristic_tags', []) if IDENTIFIER.fullmatch(t)]
        cog_rows.append({'sha256': profile['sha256'], 'bytes': profile['bytes'],
            'names': sorted({p['member'] for p in provenance}), 'games': sorted({p['game'] for p in provenance}),
            'calls': calls, 'messages': messages, 'tags': tags, 'provenance': provenance,
            'analysis_method': 'Lexical features only; no source body, parser verdict or runtime compatibility inferred.'})
    write_jsonl(corpus/'catalog'/'cogs.jsonl', cog_rows)
    note_bytes = 0
    for name, expected in REVIEWED_NOTES.items():
        raw = (source_skill/'references'/name).read_bytes()
        content = adapt_note(name, raw)
        for directory in (corpus/'notes', skill/'references'):
            directory.mkdir(parents=True, exist_ok=True)
            (directory/name).write_text(content, encoding='utf-8', newline='\n')
        note_bytes += len(content.encode())
        audit['note_reviews'].append({'note': name, 'reviewed_input_sha256': expected,
            'decision': 'Reviewed original authored analysis; exact-version gate; public commit links replace local source links; raw local evidence excluded; technical observations retained.'})
    for name in ('jk101-retail-registry.json', 'mots-retail-registry.json', 'retail-global-floats.json'):
        rows = json.loads((source_skill/'references'/name).read_text(encoding='utf-8'))
        fields = {'binary','binary_sha256','kind','name','implementation_address_or_message_id','registration_call_address','name_address','game','initial_value','initial_raw_bits','registration_helper_address','helper_type_tag','scope'}
        clean = [{k:v for k,v in row.items() if k in fields} for row in rows]
        dump(skill/'references'/name, clean)
        dump(corpus/'registries'/name, clean)
    jk = json.loads((skill/'references'/'jk101-retail-registry.json').read_text(encoding='utf-8'))
    mots = json.loads((skill/'references'/'mots-retail-registry.json').read_text(encoding='utf-8'))
    matrix = []
    for kind in ('verb','message'):
        sets = {g: {r['name']:r for r in rows if r['kind']==kind} for g,rows in [('jk',jk),('mots',mots)]}
        for name in sorted(set(sets['jk']) | set(sets['mots'])):
            matrix.append({'name': name, 'kind':kind, 'jk101':name in sets['jk'], 'mots':name in sets['mots'],
                'evidence': 'Static original-binary registration; availability is not a signature or runtime proof.'})
    write_jsonl(corpus/'registries'/'compatibility.jsonl', matrix)
    # Exactly two original helper/template files; no recursive source-skill copy.
    for rel in ('scripts/inspect_cog.py','assets/cog-test-plan.json'):
        raw=(source_skill/rel).read_bytes()
        if PRIVATE_PATTERN.search(raw.decode('utf-8')): raise ValueError('Private marker in helper '+rel)
        (skill/rel).parent.mkdir(parents=True,exist_ok=True)
        (skill/rel).write_bytes(raw)
        audit['inputs'].append({'label': rel, 'sha256':sha(raw), 'kind':'original-helper-or-template'})
    snapshot = json.loads((root/'analysis'/'summary.json').read_text(encoding='utf-8'))
    stats = {'schema':1, 'source_snapshot_utc':snapshot['generated_utc'],
        'full_local_research':{'cog_occurrences':snapshot['occurrences'],'distinct_cog_bodies':snapshot['unique_sha256'], 'redistributed_bodies':0},
        'public_export':{'source_records':len(source_rows),'distinct_cog_identity_profiles':len(cog_rows),'provenance_rows':sum(len(r['provenance']) for r in cog_rows),'compatibility_rows':len(matrix),'reviewed_adapted_notes':len(REVIEWED_NOTES),'reviewed_adapted_note_bytes':note_bytes,'total_authored_research_notes':len(REVIEWED_NOTES)+sum((corpus/'notes'/n).is_file() for n in PUBLIC_AUTHORED_NOTES),'total_authored_research_note_bytes':sum((corpus/'notes'/n).stat().st_size for n in (*REVIEWED_NOTES,*PUBLIC_AUTHORED_NOTES) if (corpus/'notes'/n).is_file())},
        'scope':'Public metadata and authored analysis. Includes only approved public-source and retail identities. No raw retail/custom script bodies or private communications are included.',
        'game_labels':'Source/catalog association, not a declaration that the body works in that engine. Use measured registry preflight and target tests.',
        'omitted_private_or_unapproved_only_profiles':omitted}
    dump(corpus/'stats.json',stats)
    for name in PUBLIC_AUTHORED_NOTES:
        path=corpus/'notes'/name
        if path.is_file():
            if PRIVATE_PATTERN.search(path.read_text(encoding='utf-8')): raise ValueError('Private marker in public-authored note '+name)
            (skill/'references'/name).write_bytes(path.read_bytes())
            audit['note_reviews'].append({'note':name,'public_authored_sha256':sha(path.read_bytes()),'decision':'Written for public edition; generalized original prose, public attribution and no private identifiers or raw communication material.'})
    # The public installed skill is a self-contained offline capsule. These are
    # the same approved metadata records, not a second or expanded source export.
    for rel in ('catalog/sources.jsonl','catalog/cogs.jsonl','stats.json'):
        target=skill/'data'/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((corpus/rel).read_bytes())
    audit['omissions']={'private_or_unapproved_only_cog_profiles':omitted,'raw_source_bodies':'all','private_messages_captures_ids_links':'all','retail_payloads':'all','third_party_manuals_and_executables':'all','unapproved_fields':'all'}
    # Defense-in-depth scan AFTER allowlisted construction. This is not the
    # publication decision and cannot confer permission to export a new source.
    generated = [corpus/'catalog'/'sources.jsonl',corpus/'catalog'/'cogs.jsonl',corpus/'stats.json',*[corpus/'registries'/n for n in ('jk101-retail-registry.json','mots-retail-registry.json','retail-global-floats.json','compatibility.jsonl')],*[corpus/'notes'/n for n in (*REVIEWED_NOTES,*PUBLIC_AUTHORED_NOTES) if (corpus/'notes'/n).is_file()]]
    for path in generated:
        data=path.read_bytes()
        if PRIVATE_PATTERN.search(data.decode('utf-8')): raise ValueError('Publication guard failed for '+path.name)
        audit['output_files'].append({'path':path.relative_to(dest).as_posix(),'bytes':len(data),'sha256':sha(data)})
    audit['scope_limit']='Records prove the recorded observed identities and authored analysis scope, not global collection completeness, rights to redistribute referenced works, or target runtime success.'
    dump(corpus/'PUBLICATION_AUDIT.json',audit)
    print(json.dumps(stats,indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-corpus',type=Path,required=True)
    p.add_argument('--source-skill',type=Path,required=True)
    p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1])
    args=p.parse_args()
    root=args.private_corpus.resolve(); dest=args.output.resolve()
    if root==dest or root in dest.parents: p.error('Output must be outside the private input corpus.')
    build(root,args.source_skill.resolve(),dest)

if __name__=='__main__': main()
