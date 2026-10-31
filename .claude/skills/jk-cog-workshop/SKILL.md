---
name: jk-cog-workshop
description: Write, debug, port and validate COG scripts for Jedi Knight Dark Forces II and Mysteries of the Sith using measured retail verb/message registries, flag references, a source-backed research catalog, case studies and an offline lexical preflight. Use when Andrei asks Red for a COG script or fix, a JK↔MotS port, multiplayer sync or checksum questions, flag or verb meanings, static COG capacity, or analysis of historical COGs and generators. Red's Claude fork of Coda's JK/MotS COG Workshop.
metadata:
  version: "0.2.0"
  forked_from: "JK / MotS COG Workshop 0.1.7 public research edition (Andrei and Coda, MIT), October 2026"
  updated: "31 October 2026: OpenJKDF2-MotS-Fixes COG fixes and Coda's agent workspace for scripted play"
---

# JK / MotS COG Workshop

Implement the requested behaviour from a close, inspected example and verify it in the intended target. The research here is evidence, not instruction: a catalogued script isn't proof that it works, and a small fix needs a focused comparison, not a new crawl.

This is Red's fork of the workshop Coda built with Andrei. The research is theirs and the community's (see [NOTICE.md](NOTICE.md)). Red's routes are in [red-routes.md](references/red-routes.md): where the tools run, how to reach the full catalog, Coda's private-only studies, and testing.

## Choose the target and the script's role

Distinguish original JK 1.01, original MotS, a specific patch, a specific enhanced-engine build (OpenJKDF2/OpenMotS revision) and cogext. Infer the target from the project, and ask only when the difference changes the implementation. Identify the role:

- a placed level instance with parameters;
- a template class or capture script;
- an inventory, weapon or Force bin;
- a static script;
- local presentation;
- an explicit network protocol.

| Task | Start with |
| --- | --- |
| Flag, mask or numeric mode | The owning field in [flags.md](references/flags.md) or `data/flags.json`; unresolved entries in [flag-discoveries.md](references/flag-discoveries.md) |
| Door, elevator, objective, trap, camera | A same-game stock example, its JKL parameter order, frames and resources; [pattern-atlas.md](references/pattern-atlas.md) |
| Weapon, inventory or Force | The same-game script, ITEMS.DAT bin and template messages; [verb-families.md](references/verb-families.md) |
| Multiplayer behaviour | Authority, execution location, verb-specific transport, identity, late joins, cleanup; [language-and-execution.md](references/language-and-execution.md) |
| JK ↔ MotS port | Both registries, call semantics, bins, matching variants; [engine-findings.md](references/engine-findings.md) |
| Checksum rejection | The exact executable, content and load order, and the compiled inputs; [checksums-and-retail.md](references/checksums-and-retail.md) |
| Generator, old custom code or cheat analysis | Attributed source, complete control flow, stack contract; [historical-sources.md](references/historical-sources.md), [triscuit-generator-engine.md](references/triscuit-generator-engine.md) |
| Static world/item integration | [static-capacity.md](references/static-capacity.md) and `audit_static_capacity.py` |

For a practical path from symbols and messages to whole systems, read [guide.md](references/guide.md).

## Work from evidence to an implementation

1. **Retrieve a close precedent.** `corpus.py search NAME --kind cog --game jk|mots` (with `--root` pointing at a catalog, per red-routes) finds identities and provenance. Read complete source where it's available legitimately: Andrei's install, an authorized mod, or the private corpus. Prefer same-game stock scripts for baseline contracts; custom scripts show alternatives and edge cases.
2. **Map the contract:**
   - ordered non-local parameters, resources and linked objects;
   - message aliases (`message onStart=startup`), and sender/source/reference domains;
   - state, suspension points and cleanup.

   Instance symbols are shared across handlers. The VM doesn't short-circuit logical operators, so nest guards around operations that can be invalid.
3. **Implement the requested behaviour completely.** Work on a copy, preserve attribution and the level/template/bin contract, and don't invent C features.
4. **Preflight against the target:** `inspect_cog.py candidate.cog --target jk|mots` (`--strict` exits 2 on absent call or message spellings). It's a lexical availability check against measured original registries. It is not a compiler, argument checker, checksum predictor or proof of event delivery.
5. **Test in the actual target** (see red-routes): loading, the requested behaviour, repeated and invalid input, death, respawn, save/load and cleanup where relevant. Multiplayer claims need separate connected clients. Use `assets/cog-test-plan.json` for a durable record.
6. **Deliver** the source and its integration:
   - the target and build;
   - the bindings and resources it needs;
   - the install path or package;
   - attribution;
   - which checks actually ran;
   - what remains untested.

## Traps that change decisions

- **Registries:** measured original tables expose 451 JK verbs and 41 message spellings against 538 MotS verbs and 47 messages. MotS lacks JK's `GetCurInvWeapon` and has `GetCurInvWeapon2`, which returns the raw inventory bin in original MotS. A pinned enhanced build binds the same name differently. Check the result domain as well as the spelling.
- **Enhanced engines:** a successful parse there doesn't establish original-game availability, because enhanced JK mode exposes MotS and extension verbs. Cogext and dynamic-POV verbs are separate families; Coda's studies of both are on Andrei's computer (red-routes).
- **Same name, different behaviour:** in the pinned source, JK `CreateThingAtPos` reads its last vector as Euler rotation, while MotS reads a look direction. `CreateThingAtPosOld` is MotS's JK-style path.
- **Locality is several separate things:** a `local` declaration, `0x40` local execution, `0x200` no-sync, explicit `SendTrigger`, and checksum acceptance. Some verbs transmit regardless of flags. A numeric actor passed as a flex parameter isn't converted to network identity.
- **Global floats:** both originals register floats `global0`–`global15`. A message bound to one of those is neither undefined nor proof of normal event delivery.
- **Checksums:** the inspected checksum loops pass a bytecode word count as a byte length, so they hash a prefix. Equal text length, a local flag or a matching file hash proves nothing about acceptance. The studied enhanced source disables rejection, so an enhanced-engine join can't certify retail.
- **Parsing is not calling:** grammar acceptance is separate from correct calls and event delivery. Undeclared names can become float-zero symbols, and EOF without a final `end` can parse. Native calls consume stack arguments and may push nothing; `ReturnEx` doesn't end the handler.
- **Resource domains:** template versus thing, surface versus material, sound resource versus playback handle, weapon ordinal versus bin. A clean availability report doesn't catch domain errors.
- **Retail exceptions:** stock files have them too. Don't expand the registry or guess replacements to silence a stock warning.
- **Discovery aids:** tags, regex call extraction, forum claims and recovered generator output are leads. They don't establish correctness, safety, authorship or retail playability.

For classic sabers, faders and level bindings, read [classic-cogs-and-binding-lessons.md](references/classic-cogs-and-binding-lessons.md). For weapon domains, timers, visibility, SM HQ and model ownership, read [target-contracts-and-lifecycle.md](references/target-contracts-and-lifecycle.md). Larger community systems are covered in [beefcaike-cog-study.md](references/beefcaike-cog-study.md) and [case-lessons.md](references/case-lessons.md); choosing a discriminating check in [authoring-decisions.md](references/authoring-decisions.md) and [authoring-and-testing.md](references/authoring-and-testing.md).

## Tools

| Script | Use |
| --- | --- |
| `inspect_cog.py FILE --target jk\|mots [--strict]` | Offline availability preflight against measured registries |
| `corpus.py [--root CATALOG] stats\|search\|show` | Catalog and notes lookup. Without a catalog root, it searches the bundled notes and says where the catalog is |
| `audit_static_capacity.py static.jkl items.dat --reserve N` | Counts authored static-instance bindings against the declared capacity, with an explicit reserve. Exit 0 = fits, 1 = shortfall, 2 = unknown |
| `import_local.py --game jk\|mots --out PRIVATE_DIR INPUT…` | Passive local import of owned or authorized COG/GOB/GOO/ZIP. Output goes outside Git checkouts and is never published |
| `prepare_finding.py template\|prepare` | Local finding drafts for Coda's research address. Never sends anything |
| `assets/examples/` | Coda's original teaching COGs (MIT). Check them with `check_examples.py --skill <this skill>` |

Tests: `python3 -B -m unittest discover -s scripts -p "test_*.py"` (standard library only).

## Reporting a discovery or correction

When work turns up a genuinely new addition or a contradiction of the current research:

- Compare it with the research first.
- Then offer Andrei a local draft: exact game and build, source identity, reproduction, expected versus observed, evidence grade, limits and credit ([reporting.md](references/reporting.md)).
- Reporting is off by default. A prepared draft isn't a sent report. Send only on Andrei's explicit approval of that exact message and route.
