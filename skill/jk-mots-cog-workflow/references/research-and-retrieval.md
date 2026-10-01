# Retrieval, local source import and evidence grades

The public package is usable without an account or network connection. Its bundled skill includes the same public catalogs under `data/` and the original authored notes under `references/`. It includes exact-byte identities and lexical metadata, not raw third-party COG bodies. Obtain full source from your owned installation or an authorized original release before adapting a complete script.

From the installed skill directory:

```text
python scripts/corpus.py stats
python scripts/corpus.py search MoveToFrame --game jk --kind cog
python scripts/corpus.py search enterbubble --game mots --kind cog
python scripts/corpus.py search checksum --kind note
python scripts/corpus.py search BeefyPack --kind source
python scripts/corpus.py show FULL_SHA256
python scripts/inspect_cog.py candidate.cog --target mots --strict
```

`search` is case-insensitive substring matching over metadata and original notes. It is not a semantic search or a compiler. `--game` filters source associations, not proven compatibility. A COG profile may appear in both game sets because identical bytes occur in both packages. `show` uses the full hash or a public source ID. `--source` is available only with an explicitly imported private corpus; a public metadata identity cannot recover absent source bytes.

For full-body work, import your own files:

```text
python scripts/import_local.py --game jk --out PRIVATE_JK GAME_DIRECTORY
python scripts/import_local.py --game mots --out PRIVATE_MOTS GAME_DIRECTORY
python scripts/corpus.py --root PRIVATE_JK search MoveToFrame --kind cog
python scripts/corpus.py --root PRIVATE_JK show FULL_SHA256 --source
```

`COG_CORPUS_ROOT` can replace repeated `--root` arguments. An existing authorized full research corpus containing `scripts/corpus_index.py` can also be selected; the wrapper delegates only stats/search/show to its local tool. The full corpus's richer options remain available through that route. No tool here starts a crawl, posts messages, publishes data or executes a downloaded game tool.

The local importer writes exact original COG bytes under hash names, retains ZIP/GOB member provenance, and reports excluded/encrypted or malformed members separately. Its output is private, including its absolute local paths. It accepts ordinary ZIP, GOB/GOO and loose COG input; it does not execute self-extractors or automatically install additional archive software. A new empty output directory avoids mixing a partial import with an earlier run. Exit 2 signals incomplete import; inspect `import-errors.json` before interpreting counts.

## Read each record at its actual evidence level

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| Public bibliography with URL/hash/status | A recorded source identity and retrieval observation | Copyright permission, current availability or successful package extraction |
| Extracted body with checked archive/member chain | Exact bytes were present in a particular container | Original sole authorship, active level use, parser acceptance or correctness |
| Lexical call/message index | Candidate spellings and useful discovery features | Argument types, control flow, resource resolution or native callability |
| Measured original registry | Names and registration addresses in an identified binary | Every call's behavior or equivalence with an enhanced engine |
| Complete source/body review | The observed branches, state transitions and integration contracts | A witnessed game session or every possible runtime input |
| Source-slice/parser probe | The tested extracted implementation under recorded adapter/build conditions | Original compiler IDs, full header loading, whole-game checksum or network outcome |
| Original-instruction emulation | Selected original instructions on the synthetic memory supplied | A launched retail process, actual level load or a connected-client result |
| Actual target observation | The named target and the specific tested scenario | Other patches, all input cases or unobserved clients |

Keep the filename, source hash, package and target distinct. A familiar filename can contain several different implementations. A community package can contain unmodified retail members. A rendered forum snippet can differ from its author's original file through formatting or truncation. Tags are discovery aids; none is a verdict that a script is safe, valid, synchronized or compatible.

## Source selection and maintenance

Use the measured target registries as the availability baseline, the [pattern atlas](pattern-atlas.md) for same-game examples, [verb families](verb-families.md) for stack-derived contracts, and [authoring decisions](authoring-decisions.md) for the next discriminating check. Historical tools and private-derived lessons are useful for hypotheses and advanced patterns, but do not replace the intended game's integration and runtime test.

The public exporter accepts only reviewed public source lanes, explicitly permitted metadata fields and approved public URL hosts. The nine adapted long-form notes are pinned by exact input hash and reviewed individually; the generalized lessons and retrieval/history notes are authored for this public edition. Link rewriting and marker scans are additional safeguards, not a substitute for deciding whether the underlying material is appropriate to publish. Raw private source, messages and communication metadata are excluded even when an original technical lesson is shared.

Research completeness is deliberately bounded. The saved snapshot has broad catalog and retail coverage, but unresolved historical payloads, private-server collection gaps and unexecuted original-game tests remain. A new catalog row or a successful lexical preflight does not close those gaps. Preserve attribution, failed leads and evidence limits when extending the corpus.
