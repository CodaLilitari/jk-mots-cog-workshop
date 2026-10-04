// Optional publisher utility. Requires Node.js and the external marked package.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
function option(name) {
  const i = args.indexOf(name);
  return i < 0 ? null : args[i + 1];
}
const output = option('--output');
if (!output || !path.isAbsolute(output)) throw new Error('Supply --output with an absolute project-assets directory.');
const modulePath = option('--marked-module');
const { marked } = await import(modulePath ? pathToFileURL(modulePath).href : 'marked');
const meta = JSON.parse(await fs.readFile(path.join(root, 'release.json'), 'utf8'));
const stats = JSON.parse(await fs.readFile(path.join(root, 'corpus/stats.json'), 'utf8'));
const base = '/projects/jk-mots-cog-workshop/';
const origin = 'https://richard-pemberton-research.darkahn.chatgpt.site';
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const css = `:root{color-scheme:dark;--bg:#0d0c11;--panel:#17141c;--line:#39333f;--text:#eae3d9;--muted:#b8afb9;--link:#a9ccd2;--accent:#c2a2d3;font:17px/1.72 system-ui,-apple-system,'Segoe UI',sans-serif;background:var(--bg);color:var(--text)}*{box-sizing:border-box}body{margin:0}a{color:var(--link);text-underline-offset:4px;overflow-wrap:anywhere}a:hover{color:#fff}a:focus-visible{outline:2px solid var(--accent);outline-offset:4px}.top{border-bottom:1px solid var(--line);background:#121016}.top-inner,main,footer{max-width:1120px;margin:auto;padding:28px 32px}.top-inner{padding-block:18px}.brand{font-weight:700;text-decoration:none;color:var(--text);margin-right:30px}nav{display:flex;align-items:center;gap:12px 25px;flex-wrap:wrap;font-size:.9rem}.eyebrow{color:var(--accent);text-transform:uppercase;letter-spacing:.12em;font-size:.78rem;font-weight:650;margin:24px 0 12px}h1,h2,h3{line-height:1.2;scroll-margin-top:24px}h1{font-size:clamp(2rem,5vw,3.5rem);letter-spacing:-.035em;max-width:24ch;margin:18px 0 24px}h2{font-size:1.7rem;margin-top:2.3em}h3{font-size:1.2rem;margin-top:1.8em}p,li{max-width:90ch}p{margin:1em 0}.lede{font-size:1.17rem;color:var(--muted);max-width:72ch}.actions{display:flex;gap:16px;flex-wrap:wrap;margin:28px 0}.button{display:inline-block;border:1px solid var(--line);padding:11px 18px;text-decoration:none;font-weight:650;border-radius:4px}.primary{background:#b5ccd0;color:#121016;border-color:#b5ccd0}.primary:hover{background:#d5e4e6;color:#121016}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin:36px 0}.card{border:1px solid var(--line);border-top:3px solid #a18aad;background:var(--panel);padding:25px}.card h2{font-size:1.35rem;margin:0 0 13px}.card p{color:var(--muted);font-size:.96rem;margin:0 0 18px}.facts{display:flex;gap:20px 38px;flex-wrap:wrap;padding:24px 0;border-block:1px solid var(--line);margin:36px 0}.facts strong{display:block;font-size:1.8rem}.facts span{font-size:.88rem;color:var(--muted)}.article{max-width:1000px}.article h1{max-width:none;font-size:clamp(2rem,4vw,3rem)}code{font-family:'Cascadia Code',Consolas,monospace;font-size:.91em;background:#211c27;padding:2px 5px;border-radius:3px}pre{padding:20px;border:1px solid var(--line);background:#17141c;overflow:auto;border-radius:5px;line-height:1.6}pre code{background:none;padding:0}blockquote{border-left:3px solid var(--accent);margin-left:0;padding:3px 22px;color:var(--muted)}.table-scroll{overflow:auto;margin:25px 0}table{border-collapse:collapse;width:100%;font-size:.9rem}th,td{border:1px solid var(--line);padding:12px 14px;vertical-align:top;text-align:left}th{background:#211c27}td code{overflow-wrap:anywhere}hr{border:0;border-top:1px solid var(--line);margin:35px 0}.scope{border-left:3px solid #8daeb5;padding:12px 22px;background:#15131a}.muted,footer{color:var(--muted)}footer{border-top:1px solid var(--line);font-size:.85rem;margin-top:50px}.skip{position:absolute;left:-10000px}.skip:focus{left:20px;top:20px;background:var(--bg);padding:15px;z-index:10}@media(max-width:680px){.top-inner,main,footer{padding-left:20px;padding-right:20px}.cards{grid-template-columns:1fr}.card{padding:21px}nav{gap:10px 17px}.brand{width:100%}.facts{gap:20px 25px}pre{padding:14px;font-size:.85rem}th,td{padding:9px}}`;
await fs.mkdir(output, { recursive: true });
await fs.writeFile(path.join(output, 'workshop.css'), css);
function shell(title, body, relative, isArticle = true) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)} — COG Workshop</title><meta name="description" content="Source-backed COG authoring for Jedi Knight: Dark Forces II and Mysteries of the Sith, with distinct target compatibility, human and machine guides."><link rel="canonical" href="${origin}${base}${esc(relative)}"><link rel="stylesheet" href="${base}workshop.css"></head><body><a class="skip" href="#main">Skip to content</a><header class="top"><div class="top-inner"><nav aria-label="Workshop"><a class="brand" href="${base}index.html">JK / MotS COG Workshop</a><a href="${base}docs/GUIDE.html">Writing guide</a><a href="${base}docs/COMPATIBILITY.html">Compatibility</a><a href="${base}docs/FLAGS.html">Flag reference</a><a href="${base}corpus/README.html">Corpus</a><a href="${base}skill/jk-mots-cog-workflow/SKILL.html">Codex skill</a><a href="${base}docs/REPORTING.html">Report a finding</a><a href="/#jk-mots-cog-workshop">Portfolio</a></nav></div></header><main id="main"${isArticle ? ' class="article"' : ''}>${body}</main><footer>Version ${esc(meta.version)} · ${esc(meta.released)} · Direction: Andrei Pemberton. Research and engineering collaboration: Coda Lilitari through Codex. <a href="${base}NOTICE.html">Sources and distribution</a> · <a href="https://gitlab.com/codalilitari/jk-mots-cog-workshop">GitLab</a> · <a href="https://github.com/CodaLilitari/jk-mots-cog-workshop">GitHub</a></footer></body></html>`;
}
function markdown(text) {
  let html = marked.parse(text, { gfm: true });
  const seen = new Map();
  html = html.replace(/<h([1-6])>([\s\S]*?)<\/h\1>/g, (_, level, content) => {
    const seed = content.replace(/<[^>]*>/g, '').replace(/&amp;/g, '').toLowerCase().replace(/[^\p{L}\p{N}\s_-]/gu, '').replace(/\s+/g, '-');
    const n = seen.get(seed) || 0; seen.set(seed, n + 1);
    return `<h${level} id="${esc(seed + (n ? '-' + n : ''))}">${content}</h${level}>`;
  });
  html = html.replace(/href="([^"\s]+)\.md(#[^"]*)?"/g, (whole, target, anchor='') => /^[a-z]+:/i.test(target) ? whole : `href="${target}.html${anchor}"`);
  html = html.replace(/<table>/g, '<div class="table-scroll"><table>').replace(/<\/table>/g, '</table></div>');
  if (/<script\b|\bon(?:click|load|error)\s*=|javascript:/i.test(html)) throw new Error('Unexpected active content in authored Markdown');
  return html;
}
const allowedTop = ['docs', 'examples', 'corpus', 'skill', 'tools', 'tests'];
const rootFiles = ['README.md', 'NOTICE.md', 'CHANGELOG.md', 'LICENSE', 'release.json', 'cog_workshop.py'];
const skipped = new Set(['__pycache__', '.pytest_cache', '.venv', 'dist', 'private', 'local-corpus', '.workshop', '.git']);
let count = 0;
async function copyOrRender(relative) {
  const source = path.join(root, relative);
  const st = await fs.lstat(source);
  if (st.isSymbolicLink()) throw new Error(`Symlink excluded: ${relative}`);
  if (st.isDirectory()) {
    for (const name of await fs.readdir(source)) if (!skipped.has(name)) await copyOrRender(path.join(relative, name));
    return;
  }
  if (/\.(pyc|tmp|building)$/.test(relative)) return;
  if (st.size > 25 * 1024 * 1024) throw new Error(`Asset exceeds Site file limit: ${relative}`);
  const target = path.join(output, relative);
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.copyFile(source, target);
  if (relative.endsWith('.md')) {
    const text = await fs.readFile(source, 'utf8');
    const title = text.match(/^#\s+(.+)$/m)?.[1] || path.basename(relative);
    const htmlRelative = relative.replace(/\.md$/, '.html').split(path.sep).join('/');
    await fs.writeFile(path.join(output, htmlRelative), shell(title, markdown(text), htmlRelative)); count++;
  }
}
for (const item of [...allowedTop, ...rootFiles]) await copyOrRender(item);
const numbers = stats.public_export;
const num = n => Number(n).toLocaleString('en-US');
const landing = `<div class="eyebrow">Public research release · ${esc(meta.version)}</div><h1>Write COGs for JKDF2 and MotS.</h1><p class="lede">A practical writing guide, a reusable Codex skill, and an attributed research corpus. Choose the target game, trace the script's contract, then build and test the behavior.</p><div class="actions"><a class="button primary" href="${base}docs/GUIDE.html">Read the writing guide</a><a class="button" href="/downloads/jk-mots-cog-workshop-${esc(meta.version)}.zip" download>Download ${esc(meta.version)}</a><a class="button" href="${base}docs/COMPATIBILITY.html">Compare JKDF2 and MotS</a></div><div class="facts"><div><strong>${num(numbers.distinct_cog_identity_profiles)}</strong><span>public COG identity profiles</span></div><div><strong>${num(numbers.source_records)}</strong><span>public source records</span></div><div><strong>${num(numbers.compatibility_rows)}</strong><span>measured compatibility rows</span></div></div><div class="cards"><section class="card"><h2>Learn to write a COG</h2><p>Follow symbols, events, state, timers, world bindings, inventory, AI and multiplayer design. Start with small original examples.</p><a href="${base}docs/GUIDE.html">Human guide →</a></section><section class="card"><h2>Keep the games distinct</h2><p>Stock JKDF2 1.01, stock MotS, enhanced engines and cogext have different contracts. Shared spellings do not guarantee the same behavior.</p><a href="${base}docs/COMPATIBILITY.html">Compatibility guide →</a></section><section class="card"><h2>Work with Codex</h2><p>Install the public skill for evidence retrieval, focused implementation and explicit validation. It coexists with a private research skill.</p><a href="${base}skill/jk-mots-cog-workflow/SKILL.html">Machine workflow →</a></section><section class="card"><h2>Read the research</h2><p>Explore reviewed notes, attributed public sources, measured registries and exact source identities. Import owned game scripts locally.</p><a href="${base}corpus/README.html">Corpus and source catalog →</a></section></div><h2>New in 0.1.5</h2><p>The <a href="${base}docs/FLAG_DISCOVERIES.html">flag discoveries</a> add fourteen bounded findings from original JK/MotS executable paths, including MotS model-face and inherited-lighting behavior. The updated <a href="${base}docs/FLAGS.html">flag reference</a> and <a href="${base}corpus/reference/flags.json">machine catalog</a> preserve separate game evidence, uncertain meanings and the full 31-family coverage. Original-static inspection does not establish runtime or multiplayer results.</p><h2>Use the workshop</h2><p>Extract the ZIP into a new folder. Python 3.10+ runs the tools; the guides are readable without it.</p><pre><code>python cog_workshop.py --offline stats\npython cog_workshop.py --offline search "SendTrigger"\npython cog_workshop.py install-skill\npython cog_workshop.py update</code></pre><p>Ordinary invocations check the portfolio feed at most once per day. Packages are checked by size and SHA-256, then installed separately from your scripts and source checkout. Use <code>--offline</code> to prevent network access. <a href="${base}docs/UPDATER.html">Read the updater behavior and recovery guide.</a></p><div class="scope"><strong>What the public release contains</strong><p>Authored notes, metadata, original examples and tools. The larger local research snapshot contains 25,364 distinct COG bodies; those bodies are not bundled here. Retail files, downloaded third-party packages and raw private history stay local. Metadata identifies sources and evidence, not blanket runtime compatibility.</p></div><h2>Report a new finding, if you choose</h2><p>Compare an addition or correction with the current research, record the exact game/build and a reproducible result, and prepare a local email draft to <strong>lilitarikiralv@gmail.com</strong>. Review the full content before choosing to send. Reporting is optional; there is no automatic sending or telemetry. <a href="${base}docs/REPORTING.html">Use the discovery reporter.</a></p><h2>Download and verify</h2><p><a href="/downloads/jk-mots-cog-workshop-${esc(meta.version)}.zip">Portfolio ZIP</a> · <a href="/updates/jk-mots-cog-workshop/SHA256SUMS.txt">SHA-256 checksum</a> · <a href="/updates/jk-mots-cog-workshop/releases.json">Automatic update feed</a> · <a href="https://gitlab.com/codalilitari/jk-mots-cog-workshop/-/releases">GitLab releases</a> · <a href="https://github.com/CodaLilitari/jk-mots-cog-workshop/releases">GitHub releases</a></p>`;
await fs.writeFile(path.join(output, 'index.html'), shell('JK / MotS COG Workshop', landing, 'index.html', false));
// Directory links in research documents resolve to usable indexes on static hosting.
async function directoryIndexes(directory) {
  const entries = await fs.readdir(directory, { withFileTypes: true });
  for (const item of entries) if (item.isDirectory()) await directoryIndexes(path.join(directory, item.name));
  if (directory === output) return;
  const relative = path.relative(output, directory).split(path.sep).join('/');
  const names = new Set(entries.map(item => item.name));
  const rows = [];
  for (const item of entries.sort((a,b) => a.name.localeCompare(b.name))) {
    if (item.name === 'index.html') continue;
    if (item.name.endsWith('.md') && names.has(item.name.replace(/\.md$/, '.html'))) continue;
    const href = item.name + (item.isDirectory() ? '/index.html' : '');
    rows.push(`<li><a href="${esc(encodeURI(href))}">${esc(item.name)}</a></li>`);
  }
  const body = `<div class="eyebrow">Research library</div><h1>${esc(relative)}</h1><p><a href="../index.html">Up one directory</a></p><ul>${rows.join('')}</ul>`;
  await fs.writeFile(path.join(directory, 'index.html'), shell(relative, body, relative+'/index.html'));
}
await directoryIndexes(output);
console.log(JSON.stringify({ rendered_markdown_pages: count, landing_page: true, version: meta.version }));
