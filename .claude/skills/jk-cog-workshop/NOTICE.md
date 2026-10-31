# Notice: JK / MotS COG Workshop, Red's fork

Forked from the public research edition of the [JK / MotS COG Workshop](https://gitlab.com/codalilitari/jk-mots-cog-workshop) 0.1.7 (commit `3dfe46b9`, released 2026-10-25), which Andrei owns and directs and Coda built in Codex. `LICENSE` is upstream's (MIT). Upstream's own notice follows, verbatim. It still governs the research, sources and distribution boundary.

## What changed in the fork

- **Verbatim from the upstream skill:**
  - `references/`, except `guide.md` and `red-routes.md`;
  - `data/flags.json`, `data/flag-discoveries.json`, `data/stats.json` and `data/recoveries/`;
  - `assets/cog-test-plan.json`;
  - the scripts `inspect_cog.py`, `import_local.py`, `audit_static_capacity.py`, `prepare_finding.py` and `test_tools.py`;
  - `assets/examples/` (upstream's original examples and their MIT `LICENSE`).
- **Edited:**
  - `scripts/corpus.py` treats the catalog as optional: notes-only search with a hint, bundled stats, and `show` refused without a catalog.
  - `references/guide.md` is upstream's `docs/GUIDE.md`, with links rewritten to this layout or to GitLab.
  - `assets/examples/README.md` has two links rewritten the same way.
- **New, by Red (MIT):** `SKILL.md` (rewritten), `references/red-routes.md`, `scripts/test_red_cog.py`.
- **Not included:**
  - the 32 MB catalog (`data/catalog/*.jsonl`); red-routes explains how to reach it;
  - upstream's `workshop.py` launcher and updater;
  - Coda's private-only references and Discord search tool, which stay on Andrei's computer and are read in place.

---

# Authorship, sources and distribution

Direction and project ownership: Andrei Pemberton. Research synthesis, tooling
and engineering collaboration: Coda Lilitari, through Codex. Original community
authors retain credit for the works studied. The workshop is an independent
research and authoring project, unaffiliated with LucasArts or the current
owners of the games and their trademarks.

The MIT license applies to the original workshop code, original examples and
authored documentation in this release. It does not relicense the games,
third-party engines, community packages, manuals, forum posts or other works
identified in the catalog. Bibliographic facts and hashes identify evidence;
they do not confer redistribution rights.

Version 0.1.7's original capacity checker and cross-project integration study
were informed by **SM Sith Lord / COG Factory**, especially the published
[P68 capacity findings](https://smsithlord.com/openjkdf2libretro/cogfactory/gen1/p68-survival-arena.html)
and [P69 integration notes](https://smsithlord.com/openjkdf2libretro/cogfactory/gen1/p69-mod-menu.html).
The study credits individual sources and preserves guest/contributor attribution.
No COG Factory implementation, artwork, game assets or unpublished tools are
included. Our source inspection and automated tests are distinct from the
author's reported results and from unperformed game tests.

This public edition contains derived research notes, source and compatibility
metadata, a human guide, a machine workflow and original tools. It deliberately
excludes owned retail source/assets and executable files, private conversation
archives, raw private messages and downloaded third-party packages. Notes may
incorporate technical lessons derived from private research without publishing
the underlying private material. These omissions are distribution boundaries,
not claims that the excluded evidence never existed.

Use the catalog to locate originals through their credited source. Supply your
own games and permitted downloads for local source inspection. Local imports
and private corpus overrides remain local and are not uploaded by the updater.

Compatibility evidence has several distinct levels: a measured registration,
source analysis, parser acceptance, a bounded implementation probe, and actual
game or multiplayer execution. Read the claim's stated level. This release
does not certify every cataloged COG, every example in retail, or all enhanced
engine and extension versions.
