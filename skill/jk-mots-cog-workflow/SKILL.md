---
name: jk-mots-cog-workflow-public
description: Write, debug, port, and validate COG scripts for Jedi Knight Dark Forces II and Mysteries of the Sith using measured retail registries, a public research catalog, source-backed case studies, and optional local game data. Use for gameplay scripts, multiplayer protocols, checksum questions, historical COG generators, and JK versus MotS compatibility.
---

# JK / MotS COG workshop

Implement the requested behavior from a close, inspected example and verify it in the intended target. The bundled corpus contains original research notes, public bibliographic metadata and exact-byte identities. It intentionally excludes raw retail scripts, copied community packages and private communications. An optional user-owned local corpus can supply complete source bodies.

For a skill installed with the Workshop's `install-skill` command, begin substantive work with `python scripts/workshop.py version`. This delegates to the registered Workshop launcher and its portfolio check, at most once per 24 hours; a newer verified release can also refresh an unchanged installed public skill. If an update occurs, reread the skill and relevant references before relying on them. Honor offline or update opt-out preferences with `--offline`, `--no-auto-update`, `COG_WORKSHOP_OFFLINE=1`, or `COG_WORKSHOP_AUTO_UPDATE=0`. Direct corpus, inspection, import and report-draft helpers remain offline; reading this skill does not itself execute an update. If the launcher is unavailable, continue with local evidence and state the freshness limit; restore or reconnect the extracted Workshop instead of creating a new updater.

## Choose the target and integration role

Distinguish original JK 1.01, original MotS, a specific patch, a specific enhanced-engine build, and cogext. Infer the target from the project; clarify when it changes the implementation. Identify whether the script is a placed level instance, template class/capture script, inventory/weapon/Force bin, static script, presentation helper, or explicit network protocol.

| Task | Evidence to start with |
| --- | --- |
| Door, elevator, objective, trap, camera | Same-game stock example, JKL parameter order, thing frames and resources; [pattern atlas](references/pattern-atlas.md) |
| Weapon, inventory or Force behavior | Same-game script, ITEMS.DAT and class/template messages; [verb families](references/verb-families.md) |
| Multiplayer behavior | Authority, execution location, verb-specific transport, object identity, late joins and cleanup; [language/execution](references/language-and-execution.md) |
| JK ↔ MotS port | Both measured registries, call semantics, bins and matching source variants; [engine findings](references/engine-findings.md) |
| Retail checksum rejection | Exact executable/content/load order and actual compiled inputs; [checksum evidence](references/checksums-and-retail.md) |
| Generator, old custom code, or cheat analysis | Attributed source, complete control flow, native stack contract and target; [historical sources](references/historical-sources.md) and [generator study](references/triscuit-generator-engine.md) |

## Work from evidence to an implementation

1. **Retrieve a close precedent.** Run `python scripts/corpus.py search MoveToFrame --game jk --kind cog`. `show HASH` returns metadata; with an imported private local corpus, `show HASH --source` prints owned source. Public catalog records are discovery and identity evidence, not executable examples or compatibility approvals.
2. **Map the contract.** Record ordered nonlocal parameters, resources, linked objects, event aliases, sender/source/reference domains, state, suspension points and cleanup. Read complete relevant source when available. An absent native spelling can still parse; parser acceptance does not make it callable.
3. **Implement the requested behavior completely.** Preserve attribution and integration contracts; work on a copy of historical source. Use nested guards for potentially invalid operations: the pinned VM does not short-circuit logical operators. Instance symbols are shared across handlers and are not C stack locals.
4. **Run target preflight.** `python scripts/inspect_cog.py candidate.cog --target jk` or `--target mots` reports measured verb/message availability and lexical dependencies. `--strict` exits 2 for absent call/message spellings. This is not a compiler, argument checker, checksum predictor or proof of event delivery.
5. **Test in the actual target.** Verify loading, requested behavior, repeated/invalid input, and relevant death, respawn, save/load or cleanup paths. Multiplayer claims require separate connected clients and remote observations. Use [authoring/testing](references/authoring-and-testing.md) and `assets/cog-test-plan.json` for a durable record.
6. **Deliver the source and integration.** State target game/build, required resources and bindings, installation/package location, attribution, executed checks and untested cases. Separate original-binary inspection, source probes, original retail execution and connected-client observations.

## Findings that materially change authoring

- The measured original tables expose 451 JK verbs/41 message spellings versus 538 MotS verbs/47 message spellings. Alias counts are not distinct event counts. MotS adds 88 verb spellings and omits JK's `GetCurInvWeapon`; it exposes `GetCurInvWeapon2`. A same-named verb can still have target-specific semantics.
- In the pinned source, JK `CreateThingAtPos` interprets its final vector as Euler rotation; MotS uses a look direction. `CreateThingAtPosOld` is MotS's JK-style source path. This is implementation evidence, not an all-version runtime test.
- A `local` symbol declaration, `0x40` local execution, `0x200` no-sync, explicit `SendTrigger`, and checksum acceptance are separate mechanisms. Generic float trigger parameters do not automatically convert a thing index to network identity.
- Native calls consume stack arguments and may push no result. `ReturnEx` sets a response without ending the handler. Unknown native calls can leave evaluated arguments on the stack; arbitrary-looking historical padding needs control-flow and stack analysis.
- A message alias can bind a different label (`message onStart=startup`). Both original binaries also register float globals `global0`–`global15`; these are not additional normal events. Check actual routes and labels.
- The inspected original checksum loops pass a bytecode word count as a byte length, hashing a prefix. Neither equal text length nor local flags establish compatibility. The pinned enhanced source disables the rejection branch and has a MotS personality callback difference; an enhanced join cannot prove retail acceptance.
- Resources have distinct domains: template versus thing, surface versus material, sound resource versus playback handle, weapon ordinal versus inventory bin. A clean availability report does not catch these errors.
- Check existence, loading and reachability separately. A packaged alternative can be unused, comments can promise retransmission absent from the body, and a future timer does not stop current fallthrough.

Use [authoring decisions](references/authoring-decisions.md) to select a discriminating check, [BeefCaike's integration study](references/beefcaike-cog-study.md) for substantial community systems, and [generalized recovered lessons](references/case-lessons.md) for advanced lifecycle, cache and protocol pitfalls.

## Portable retrieval and private data

The default `scripts/corpus.py` searches `data/` and these references, with no network. `COG_CORPUS_ROOT` or `--root PATH` selects another corpus; an existing full research corpus with `scripts/corpus_index.py` is delegated to for read-only stats/search/show. To import owned retail or authorized custom files locally, use `python scripts/import_local.py --game jk --out PRIVATE_DIRECTORY GAME_DIRECTORY` (or `--game mots`). It reads ZIP/GOB/GOO/COG files passively, bounds archive members and stores original COG bytes by hash. Do not publish that private output by default. See [retrieval and evidence grades](references/research-and-retrieval.md).

The public skill is named separately so installation does not overwrite an existing private `jk-mots-cog-workflow` skill. Research notes can be extended from authorized private evidence in original words; raw private material and identifying communication metadata remain local.

## Optional discoveries and corrections

When an implementation produces genuinely new, additional or contradictory understanding, first compare it with the current corpus and record why it changes the existing account. Offer a local finding draft with exact game/build, source identity, reproduction, expected versus observed result, evidence grade, limits and credit. The intended report recipient is `lilitarikiralv@gmail.com`. Reporting is off by default. Use [the reporting workflow](references/reporting.md) to prepare and review the exact recipient, subject, body and any proposed attachments. Never send automatically; sending requires the user's explicit per-report instruction through an available authorized email route. A prepared draft is not a sent report. Omit private source/capture material and identifying communication metadata from reports unless the owner explicitly authorizes those exact items for that recipient.
