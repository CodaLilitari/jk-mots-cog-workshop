# Red's routes for COG work

The workshop's tools are standard-library Python 3.10+. They run in the device shell on Andrei's computer (beside his levels and mods) or in the cloud workspace. On the device, mirror the skill's layout once per session under `$HOME/.red-tools/jk-cog/` with quoted heredocs: scripts in `scripts/`, and the three registry JSON files in `references/`, because `inspect_cog.py` reads `../references/` from its own location. Never run tools inside Andrei's or Coda's checkouts, and never run Git there.

## The research catalog

The public catalog (`cogs.jsonl` 21 MB, `sources.jsonl` 11 MB) holds exact identities, calls, messages and provenance for about 21,000 COG bodies. It isn't bundled. Without it, `corpus.py search` covers the bundled notes and prints a hint.

1. **Andrei's local checkout** (read-only), on the device, from whichever connected folder holds it:

   ```text
   python3 -B $HOME/.red-tools/jk-cog/scripts/corpus.py --root "$HOME/mnt/<folder>/jk-mots-cog-workshop/skill/jk-mots-cog-workflow/data" search MoveToFrame --kind cog --game mots --limit 10
   ```

2. **Release 0.1.7 from GitLab,** into the cloud workspace, pinned and checked:

   ```text
   B=https://gitlab.com/codalilitari/jk-mots-cog-workshop/-/raw/3dfe46b9ecba8f57acc65645b025e607708463b4/skill/jk-mots-cog-workflow/data
   mkdir -p <scratchpad>/cog-catalog/catalog
   curl -fsSL -o <scratchpad>/cog-catalog/catalog/cogs.jsonl "$B/catalog/cogs.jsonl"
   curl -fsSL -o <scratchpad>/cog-catalog/catalog/sources.jsonl "$B/catalog/sources.jsonl"
   curl -fsSL -o <scratchpad>/cog-catalog/stats.json "$B/stats.json"
   sha256sum <scratchpad>/cog-catalog/catalog/*.jsonl
   #   015f8e1bf571942b9ab604a0714af9a347ada6d7999f6c1b403cfba5203f6fea  cogs.jsonl
   #   57de8996f15a4241f10ed156a3326715549679dc68d922db417d4ce3fe7e0998  sources.jsonl
   python3 -B scripts/corpus.py --root <scratchpad>/cog-catalog search SendTrigger --kind cog --game jk
   ```

3. **The private research corpus,** a folder on Andrei's computer that holds owned retail source bodies and private archives. Ask him where it is. Use it only when a task needs complete source text:
   - Request access to that one folder.
   - Only `stats`, `search` and `show` (`show HASH --source` prints a body), always with `python3 -B` so nothing is written there. `corpus.py` hands those commands to the corpus's own index script.
   - Never build, import or crawl in it.
   - Quote retail or private source to Andrei only as far as the task needs. It is never published.

A catalog row is identity and discovery evidence. It doesn't mean the script works, is safe, is by its listed author, or is retail-compatible.

## Owned retail or mod files

`import_local.py --game jk|mots --out PRIVATE_DIR INPUT...` reads COG, GOB, GOO and ZIP inputs passively and stores original bytes by hash.

- **`PRIVATE_DIR`** must be outside any Git checkout. Use Red's own folder, or a private folder Andrei names.
- **Don't publish or redistribute** the output.
- **It doesn't overwrite:** re-importing into the same directory is refused, so use a new one.

## Coda's private-only references

Coda's local copy of this workflow has studies that the public release leaves out, and so does this fork: cogext registrations and their stack effects, the dynamic POV verbs, the stock Force Speed and Protection scripts, historical custom-script and integration cases, the historical archives, and the language's design history. When a task touches one of those subjects, ask Andrei, then read the study in place on his computer, read-only. Never copy it into anything shared.

Coda's `search_recent_discord.py` searches her Discord captures. It isn't part of this fork, and Red doesn't read those captures. If recent community evidence matters, ask Andrei or use the private corpus index.

## Testing in the target game

Red can run OpenJKDF2-MotS-Fixes in her cloud workspace once Andrei supplies his game files (the **jk-level-workshop** skill's engine route, `references/openmots-linux.md` there). Two interfaces, each with its own reach:

- **A posed still (capture-v1):** a few frames in, from one camera. It can show a COG's startup-visible effect, such as a light or texture it sets at startup, and nothing more.
- **Scripted play (Coda's agent workspace, 30 October 2026):** a live single-player session driven through ordinary keys, mouse and menus, with read-only state (level, player position, health, sector) and screenshots, plus JSON scenario recipes with assertions and a report. This exercises activation, trigger, timer and pulse paths that real play reaches. It runs in real time, so outcomes can vary between runs; it can't run console code, teleport, or step time, and it doesn't cover multiplayer or sound. It shows OpenJKDF2 behaviour on Red's software renderer, not retail behaviour.

- **Who tests:** Andrei does, from an exact test case written with `assets/cog-test-plan.json`. Or Coda runs her harness or capture tools, from a handoff file in the project folder. Or Red uses computer use on Andrei's desktop when he asks: never while he's playing, and record the executable and profile.
- **Multiplayer claims need separate connected clients:** remote observers, repeats, death and respawn, late join, cleanup.
- **Keep the evidence levels separate:** lexical preflight, parser acceptance, source analysis, original-binary inspection, retail execution, connected-client observation.

## Engine changes worth knowing (OpenJKDF2-MotS-Fixes main, 29 October 2026)

When a COG behaves differently in OpenJKDF2 than in retail, check which engine build was used. Recent fixes on the fork's `main` (some merged from upstream OpenJKDF2):

- **`VectorCross` operand order** (upstream #492, ported from the fork). COG verbs pop their arguments right to left, and OpenJKDF2 returned `b × a` for `VectorCross(a, b)`. JK.EXE and JKM.EXE return `a × b`: `VectorCross('1 0 0', '0 1 0')` gives `'0 0 1'` in retail and gave `'0 0 -1'` in older OpenJKDF2 builds. A script tuned against an old build has the opposite sign.
- **COG stack overflow shift** (fork PR #6). When a COG's stack was full, older builds shifted it with a byte count based on the whole array (or, with dynamic stacks, the pointer) instead of one symbol. A script that overfills its stack could corrupt memory there.
- **Game clocks during physics substeps** (`5f4270b0`). COG and event consumers could read an outer-frame seconds clock that didn't match the substep they ran in. Timing-sensitive scripts can differ between builds before and after this fix.
- **Static thing templates** (upstream #485 and #475). Missing static templates could corrupt sectors, and template indices could crash a MotS restart.

Record the engine commit with any OpenJKDF2 result. Retail behaviour still needs retail evidence.

## Findings

`prepare_finding.py template` and then `prepare` write a local draft to Coda's research address (`lilitarikiralv@gmail.com`).

- **Sending:** only after Andrei approves that exact recipient, subject, body and attachment list, through a route he names. Red never sends it on her own.
- **Leave out:** private source text and communication metadata, unless he authorizes those exact items.
