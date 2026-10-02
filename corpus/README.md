# Public COG research corpus

This initial release publishes substantive original analysis, measured JK/MotS registries, a source bibliography and exact COG identity/lexical metadata. It does not redistribute raw retail scripts, community packages, copied manuals, private messages or capture data. Public availability of a referenced work is not a blanket redistribution license.

The frozen local research snapshot contains 70,346 COG occurrences and 25,364 distinct bodies. The public subset is deliberately smaller: consult [stats.json](stats.json) for generated counts. It contains only identities with approved public-source or retail provenance. Game labels on catalog records describe that provenance; they do not prove that every packaged script works in the named engine.

| Public artifact | What it provides |
| --- | --- |
| [catalog/sources.jsonl](catalog/sources.jsonl) | Public source URL, limited title/author/category metadata, recorded response size/hash and status where available. No page text, message text or nested capture metadata. |
| [catalog/cogs.jsonl](catalog/cogs.jsonl) | Exact COG hash/size, public or retail member names, game associations, lexical calls/messages/tags and approved provenance IDs. No source bodies, declarations or literal string data. |
| [registries/compatibility.jsonl](registries/compatibility.jsonl) | Per-name JK 1.01 versus MotS availability for native verbs and integer message spellings. |
| [registries/jk101-retail-registry.json](registries/jk101-retail-registry.json) and [MotS registry](registries/mots-retail-registry.json) | Measured binary hashes, registration/name addresses and implementation address or message ID. No executable or disassembly payload. |
| [notes/](notes/) | Original research on language/execution, target differences, checksums, 15 verb families, 21 retail examples, historical generators, community integration and generalized lessons from authorized private research. |
| [PUBLICATION_AUDIT.json](PUBLICATION_AUDIT.json) | Approved input identities, exact-version note gates, output hashes, exclusions and scope limits. |

The registry union has 539 verb spellings and 47 message spellings. Original JK has 451/41, original MotS 538/47; aliases count as spellings. The full source-specific explanation is in [engine findings](notes/engine-findings.md). Metadata lookup and availability checks work offline through the bundled skill scripts.

## Research checkpoint in 0.1.2

The [classic COG and binding study](notes/classic-cogs-and-binding-lessons.md) adds original analysis of public historical material and measured registries. The large catalog remains the frozen snapshot described above. Newly captured private material is not added to this public catalog or represented as a complete search of any server. Acquisition is paused at this release checkpoint; standalone fader variants, a separately identified CL0wN maker, the missing Sanctium package and uncensored SM Purgatory remain recovery gaps. Those gaps are not evidence of nonexistence.

## Optional local source import

Use your own installation or another source you are authorized to inspect. From the release root:

```text
python skill/jk-mots-cog-workflow/scripts/import_local.py --game jk --out PRIVATE_JK GAME_DIRECTORY
python skill/jk-mots-cog-workflow/scripts/import_local.py --game mots --out PRIVATE_MOTS GAME_DIRECTORY
python skill/jk-mots-cog-workflow/scripts/corpus.py --root PRIVATE_JK search MoveToFrame --kind cog
python skill/jk-mots-cog-workflow/scripts/corpus.py --root PRIVATE_JK show FULL_SHA256 --source
```

The importer accepts explicit files or recursively inventories the explicit directory for `.cog`, `.gob`, `.goo` and `.zip`. It verifies GOB directory/member bounds, ZIP CRCs, fixed expansion/depth limits and immutable object hashes. It never executes scripts or installers. Unsupported/encrypted containers and failed members are reported in `import-errors.json`; exit 2 means the import is incomplete. Choose a new empty output directory. The output is marked private, contains the original local paths in its provenance, and is not included by the public exporter.

For custom public packages, locate the original credited release through the bibliography, check its terms and obtain it through a supported download route. Import the exact local file and compare its SHA-256 with the catalog. A matching package hash proves identity with that recorded package, not game correctness or a redistribution license. The release does not silently fetch anything or resume research.

## Reproduce the public projection

Maintainers with the authorized source corpus and exact reviewed skill revision can run:

```text
python tools/export_public_corpus.py --private-corpus PRIVATE_CORPUS --source-skill SOURCE_SKILL --output PUBLIC_WORKSHOP
```

The exporter selects explicit public source lanes and fields, validates public URL hosts/query keys, omits private-only provenance and pins each reviewed authored note by hash. Changed notes require fresh review. Its final marker scan is defense in depth, not the basis for deciding what is safe to publish. Original release notes and portable helpers are maintained directly in this repository. Future exports must preserve the same private/public distinction.

Every raw artifact excluded for privacy or rights reasons remains excluded even when its lessons inform original technical notes. The public research does not imply a fresh retail launch, a verified multiplayer session, complete archive recovery or universal engine compatibility.
