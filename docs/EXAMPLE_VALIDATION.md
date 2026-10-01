# Initial example validation

The six original teaching examples were checked on 1 October 2026 UTC. They are **not represented as retail-playtested or multiplayer-ready**. Their declared targets are the target registrations and inspected implementation contracts used while authoring them.

## Completed checks

| Check | Executed result | Scope |
| --- | --- | --- |
| Native/message spelling preflight | 10 intended-target checks passed with zero absent spellings and zero inspector warnings | Four shared examples on both original-game tables, plus one weapon diagnostic on its own target |
| Deliberately wrong target | 2 expected incompatibilities detected | JK weapon diagnostic reports `getcurinvweapon` absent in MotS; MotS diagnostic reports `getcurinvweapon2` absent in JK |
| Pinned parser/code generator | All 6 code sections accepted with zero syntax errors | Generated lexer/parser and extracted AST/codegen at commit `b1be98bd4f170b5384cb71b15443a274aac6a937`, host/symbol adapters, GCC with undefined-behavior sanitizer |
| Source contract review | Authored calls and link/timer/state design compared with the inspected implementation and measured registries | Not a dynamic test of those game behaviors |

The [availability receipt](example-availability.json) records the example hashes, exact targets, expected wrong-target findings and inspector hash. The [parser receipt](example-parser-results.json) records source-unit hashes, adapter hashes, compile options, example hashes and each parser result. These are offline receipts, not simulated game results.

The parser adapter only compiles code sections. It does not load `symbols`, resolve resources, assign original native symbol IDs, execute the VM, load a retail episode or connect clients. The adapter is retained in the research checkout and is not bundled in this initial release. Its recorded result is therefore inspectable evidence, while the shipped lexical check below is directly repeatable from this package.

## Repeat the shipped availability check

From the release root:

```text
python examples/check_examples.py
```

The checker uses `skill/jk-mots-cog-workflow/scripts/inspect_cog.py` by default and accepts `--skill PATH` for another installation. It uses no network and requires no third-party Python modules. `--output PATH` writes a receipt containing relative example paths. It verifies that the wrong-game weapon diagnostics fail for the intended missing spelling, rather than silently treating every file as portable.

## Still required in the intended game

| Example | Meaningful runtime checks |
| --- | --- |
| Counter | Load the actual instance; activate repeatedly; verify a fresh level starts at zero |
| Timed light | Confirm configured off/on extra light, timeout, ignored repeat activations and a second full cycle; test the project's save/reload expectations |
| Two-stop mover | Confirm initial frame 0, travel both ways, ignored activation while moving, real blocking event, stopped state and retry to the same destination |
| AI destination | Confirm a valid actor/marker, path access, actual movement, competing combat goals and the intended behavior when navigation fails |
| JK weapon diagnostic | Select several JK weapons and compare printed values to the same-game inventory setup |
| MotS weapon diagnostic | Select several MotS weapons and compare values to its own selection/bin setup |

The mover uses the ordinary linked-reference mask and teaches player-triggered obstruction handling; other source types and specialized collision behavior require explicit mask/event review. None of the examples includes a complete multiplayer authority, late-join or state-recovery design. If those features are added, their test scope must grow accordingly.
