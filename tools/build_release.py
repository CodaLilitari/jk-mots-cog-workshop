"""Build a deterministic, allowlisted public workshop ZIP and portfolio feed."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('tools', 'tests', 'docs', 'examples', 'corpus', 'skill')
ROOT_FILES = ('.gitignore', '.gitattributes', 'README.md', 'LICENSE', 'NOTICE.md', 'CHANGELOG.md',
              'release.json', 'cog_workshop.py')
EXTENSIONS = {'.py', '.md', '.json', '.jsonl', '.txt', '.cog', '.yaml', '.yml',
              '.toml', '.mjs', '.css', '.html'}
EXCLUDED_PARTS = {'__pycache__', '.pytest_cache', '.venv', 'dist', 'private',
                  'local-corpus', '.workshop', '.git', 'node_modules'}
FORBIDDEN = {
    'private Discord permalink': re.compile(r'https?://(?:\w+\.)?discord(?:app)?\.com/channels/\d+', re.I),
    'raw Discord attachment URL': re.compile(r'https?://(?:cdn|media)\.discordapp\.(?:com|net)/attachments/', re.I),
    'personal Windows path': re.compile(r'[A-Z]:[/\\]+Users[/\\]+Andrei(?:[/\\]|\b)', re.I),
    'Git hosting token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|glpat-[A-Za-z0-9_-]{20,})'),
    'temporary signed delivery URL': re.compile(r'https?://[^\s"<>]*(?:oaiusercontent\.com|[?&](?:X-Amz-Signature|sig|token)=)', re.I),
    'private receiver address': re.compile(r'https?://127\.0\.0\.1:877[67]/', re.I),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def public_files(root: Path) -> list[Path]:
    paths = [root/name for name in ROOT_FILES]
    for folder in DIRECTORIES:
        base = root/folder
        if not base.is_dir():
            raise ValueError(f'Missing release directory: {folder}')
        paths.extend(p for p in base.rglob('*') if p.is_file()
                     and not EXCLUDED_PARTS.intersection(p.relative_to(root).parts)
                     and p.suffix.lower() not in {'.pyc', '.pyo', '.tmp', '.building'})
    names = set()
    for path in paths:
        name = path.relative_to(root).as_posix()
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f'Not a regular in-root release file: {name}')
        if path.name not in ROOT_FILES and path.suffix.lower() not in EXTENSIONS:
            raise ValueError(f'Unreviewed file type: {name}')
        if name.casefold() in names:
            raise ValueError(f'Case-insensitive duplicate: {name}')
        names.add(name.casefold())
        data = path.read_bytes()
        try:
            text = data.decode('utf-8-sig')
        except UnicodeDecodeError as exc:
            raise ValueError(f'Public release text must be UTF-8: {name}') from exc
        for label, pattern in FORBIDDEN.items():
            if pattern.search(text):
                raise ValueError(f'Publication scan found {label} in {name}')
    return sorted(paths, key=lambda p: p.relative_to(root).as_posix())


def build(root: Path, output: Path) -> dict:
    meta = json.loads((root/'release.json').read_text(encoding='utf-8'))
    assert meta['schema_version'] == 1 and meta['product'] == 'jk-mots-cog-workshop'
    version = meta['version']
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('This publisher requires a stable three-part version')
    paths = public_files(root)
    members = [{'path': p.relative_to(root).as_posix(), 'size': p.stat().st_size,
                'sha256': sha(p.read_bytes())} for p in paths]
    manifest = {'schema_version': 1, 'product': meta['product'], 'version': version,
                'scope': 'Allowlisted public release; excludes raw private history, retail payloads and third-party package bodies.',
                'files': members}
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False)+'\n').encode('utf-8')
    output.mkdir(parents=True, exist_ok=True)
    filename = f'jk-mots-cog-workshop-{version}.zip'
    package = output/filename
    temporary = package.with_suffix('.zip.building')
    def write(z, name, data):
        info = zipfile.ZipInfo(name, (2026, 10, 1, 0, 0, 0))
        info.create_system = 3
        info.external_attr = (stat.S_IFREG | 0o644) << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, data, compresslevel=9)
    with zipfile.ZipFile(temporary, 'w') as z:
        for path in paths:
            write(z, path.relative_to(root).as_posix(), path.read_bytes())
        write(z, 'FILES.sha256.json', manifest_bytes)
    with zipfile.ZipFile(temporary) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(members)+1
        for member in members:
            data = z.read(member['path'])
            assert len(data) == member['size'] and sha(data) == member['sha256']
    temporary.replace(package)
    digest = sha(package.read_bytes())
    primary = f'https://richard-pemberton-research.darkahn.chatgpt.site/downloads/{filename}'
    feed = {'schema_version': 1, 'product': meta['product'], 'latest': {
        'version': version, 'url': primary, 'size': package.stat().st_size, 'sha256': digest,
        # Only independently reachable public distribution is advertised to clients.
        # A GitHub repository/release upload alone does not establish anonymous access.
        'mirrors': [f'https://gitlab.com/codalilitari/jk-mots-cog-workshop/-/releases/v{version}/downloads/{filename}']}}
    (output/'FILES.sha256.json').write_bytes(manifest_bytes)
    (output/'releases.json').write_text(json.dumps(feed, indent=2)+'\n', encoding='utf-8')
    (output/'SHA256SUMS.txt').write_text(f'{digest}  {filename}\n', encoding='utf-8')
    result = {'version': version, 'filename': filename, 'size': package.stat().st_size,
              'sha256': digest, 'file_count': len(members)+1,
              'uncompressed_bytes': sum(m['size'] for m in members)+len(manifest_bytes),
              'publication_scan': 'passed; field allowlisting and editorial review remain separate requirements'}
    (output/'build-receipt.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=ROOT)
    ap.add_argument('--output', type=Path, default=ROOT/'dist')
    args = ap.parse_args()
    print(json.dumps(build(args.root.resolve(), args.output.resolve()), indent=2))
