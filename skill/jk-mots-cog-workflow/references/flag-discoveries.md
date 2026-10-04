# JKDF2 and MotS: unresolved flag findings

Research dated 2026-10-03, published in **COG Workshop 0.1.5**. This supplement extends the 0.1.4 audit; its findings are incorporated in the matching main-catalog entries.

This pass produced **14 bounded findings with original-executable evidence for at least one target, including two newly mapped original-MotS rendering paths**. Some establish a missing behavior; others correct a misleading alias or separate an event from a persistent flag. They do not prove every meaning of every bit.

Original-static means selected code paths in the exact original JK1.01 and MotS executables, checked against their bytes. It does not mean the game was run or multiplayer behavior was tested. Original JK and MotS evidence remains separate; the new rendering paths are established for MotS only within the compared routines. The matching main-catalog rows summarize these findings; this supplement supplies the full evidence and limits.

## Findings by field

| Field/value | Finding | Original JK1.01 | Original MotS |
| --- | --- | --- | --- |
| thing `0x00010000` | Level-placement exclusion in the non-multiplayer loading branch | Verified code path | Verified code path |
| thing `0x80000000` | One deferred eligible thing in the MotS renderer | Absent from compared routine | Verified code path |
| surface `0x00000080` | Suppress the inspected surface-collision impact damage | Verified code path | Verified code path |
| physics `0x00020000` | Skip initial velocity rotation on creation | Verified code path | Verified code path |
| actor `0x00002000` | Eligibility for the saber-blocking branch | Verified code path | Verified code path |
| actor `0x00200000` | Gate player controls, with different look handling | Verified code path | Verified code path |
| ai `0x00000020` | Fire-target state maintained by AISetFireTarget | Verified code path | Verified code path |
| ai `0x00000100` | Mode-change event; persistent-mode meaning remains unproved | Verified code path | Verified code path |
| jk `0x00000040` | Consume-once saber hit-history reset | Verified code path | Verified code path |
| jk `0x00000100` | MotS bubble-owner registration marker | Not established | Verified code path |
| multiplayer `0x00000002` | Conditional same-team player health-damage suppression | Verified code path | Verified code path |
| weapon `0x00010000` | Select the special collision/trail update handler | Verified code path | Verified code path |
| face `0x00000010` | Initial model-face lighting-mode override | Absent from compared routine | Verified code path |
| light `0x00000006` | Inherit and propagate a stored mesh lighting scalar | Absent from compared routines | Verified code path |

The table identifies fields as well as values: `thing`, `actor`, `physics`, `jk`, and AI state are different namespaces. Light mode 6 is a scalar value. Descriptive names below are research labels, not recovered developer symbols.

## thing 0x00010000: Level-placement exclusion in the non-multiplayer loading branch

The loader adds this bit to its rejection mask when submode bit 1 is clear. A populated level thing whose flags intersect that mask is freed. The corresponding multiplayer branch adds 0x8000 instead. Source multiplayer startup sets the submode bit, supporting the shorthand single-player placement exclusion.

**Limits and authoring consequence.** This is a loading condition. Setting it after loading does not by itself hide or destroy the thing. The precise original predicate is submode bit 1 clear; other rejection bits, including difficulty, still apply.

Evidence anchors: `JK 0x4CEC5D-0x4CEC70 and 0x4CEE07-0x4CEE1A`; `MotS 0x51D36B-0x51D37E and 0x51D527-0x51D53A`; `World/sithThing.c:1547-1552,1599-1601; Dss/sithMulti.c:211`.

Existing source alias: `SITH_TF_10000`. Evidence grade: `original-retail-static`.

## thing 0x80000000: One deferred eligible thing in the MotS renderer

Original MotS stores an eligible flagged thing in one local pointer slot and skips its ordinary draw. Later eligible flagged things overwrite that slot. After normal traversal, the final stored thing is drawn once. The corresponding complete JK1.01 routine lacks this test and slot.

**Limits and authoring consequence.** This is not a queue for all flagged things, and it does not establish through-wall rendering. Earlier eligibility/clipping applies. The inspected JK difference is function-specific, not proof of game-wide bit nonuse. No visual runtime result is claimed.

Evidence anchors: `MotS 0x516270,0x5166B5-0x516719`; `JK corresponding routine 0x4C7DD0-0x4C8241 (end exclusive)`; `Engine/sithRender.c:2736-2737,2970-2997`.

Existing source alias: `SITH_TF_80000000`. Evidence grade: `original-retail-static`.

## surface 0x00000080: Suppress the inspected surface-collision impact damage

For the inspected physics thing-versus-surface collision path, the surface bit becomes the fourth argument to the collision response. A set bit bypasses that response branch's impact-damage calculation, hit-damaged sound and FALL-class DamageThing call.

**Limits and authoring consequence.** The collision response itself still runs. This is not universal damage immunity or a guarantee that every source of fall damage honors the bit. The flagged surface must be the actual contact surface in this path.

Evidence anchors: `JK 0x4E8E0D,0x4E8E27,0x4E9707-0x4E9767`; `MotS 0x5365BD,0x5365D7,0x536ED3-0x536F33`; `Engine/sithCollision.c:916-929,1120-1127`.

Existing source alias: `SITH_SURFACE_80`. Evidence grade: `original-retail-static`.

## physics 0x00020000: Skip initial velocity rotation on creation

In CreateThingAtPos, a physics thing normally has its initial velocity transformed by its created orientation. A set 0x20000 skips that transform in both originals.

**Limits and authoring consequence.** This is not a general angular-velocity, continuous-spin or object-orientation disable flag. MotS can apply the COG-supplied look vector after native creation; the transform uses the orientation at native creation time, not necessarily the final look-vector orientation. Setting the flag later does not undo the transform.

Evidence anchors: `JK 0x4CDF28-0x4CDF47; registered CreateThingAtPos 0x502520`; `MotS 0x51C644-0x51C663; registered CreateThingAtPos 0x552E00`; `World/sithThing.c:1107-1108`.

Existing source alias: `SITH_PF_20000`. Evidence grade: `original-retail-static`.

## actor 0x00002000: Eligibility for the saber-blocking branch

The saber-hit path checks this bit on an actor/player being hit before admitting it to field-of-view and chance-based blocking checks, which also reject an invisible attacker. A clear bit goes to the damage path.

**Limits and authoring consequence.** The bit permits this blocking path; it does not guarantee a block. BLEEDS is a misleading source alias for this inspected JK/MotS consumer. Other possible consumers have not been exhaustively excluded.

Evidence anchors: `JK 0x40BD9F-0x40BDA8 and following blocking checks`; `MotS 0x40D303-0x40D30C and following blocking checks`; `Gameplay/jkSaber.c:264-307`.

Existing source alias: `SITH_AF_BLEEDS; historical THING_TYPEFLAGS_ISBLOCKING`. Evidence grade: `original-retail-static`.

## actor 0x00200000: Gate player controls, with different look handling

On the inspected player control path, a set bit skips movement, activation and map handling. Original JK calls its look handler before the flag gate. Original MotS places the look call after the gate, so the flagged path skips it as well.

**Limits and authoring consequence.** This controls processing of these inputs; it does not freeze all physics or prevent every scripted move. Preserve the JK/MotS difference instead of reducing the meaning to immobile.

Evidence anchors: `JK look call 0x4D8C5F; gate 0x4D8C6F-0x4D8C79`; `MotS gate 0x527852-0x52785C; look call 0x5278A3`; `Devices/sithControl.c:1025-1053`.

Existing source alias: `SITH_AF_CONTROLSDISABLED; historical THING_TYPEFLAGS_IMMOBILE`. Evidence grade: `original-retail-static`.

## ai 0x00000020: Fire-target state maintained by AISetFireTarget

AISetFireTarget stores the target pointer and timestamp, then sets this AI-control-block bit when the target is non-null and clears it otherwise. If the flags change, it emits the mode-change event. Both original wrappers agree.

**Limits and authoring consequence.** TOUGHSKIN is not evidence of armor here. Setting the bit alone does not assign a target pointer or cause firing; use AISetFireTarget. Other possible consumers are not exhaustively excluded.

Evidence anchors: `JK AISetFireTarget 0x501550; writes 0x501584-0x5015B4`; `MotS AISetFireTarget 0x551C30; writes 0x551C64-0x551C94`; `Cog/sithCogFunctionAI.c:389-424`.

Existing source alias: `SITHAI_MODE_TOUGHSKIN`. Evidence grade: `original-retail-static`.

## ai 0x00000100: Mode-change event; persistent-mode meaning remains unproved

The inspected use is an AI event identifier and instinct event-subscription mask. AISetMode emits event 0x100 whenever its OR changes the mode word. The event dispatcher sends COG AIEVENT with first extended parameter 256.0 in original JK, but current AI flags converted to float in original MotS.

**Limits and authoring consequence.** This resolves an event role, not a special persistent AI mode. Generic mode setters can store 0x100; that does not prove a dedicated mode behavior. The dispatcher has living/class/disabled/sleeping gates. MotS float conversion need not preserve every high-bit integer exactly.

Evidence anchors: `JK AISetMode 0x5011E0; dispatcher 0x4EA26D-0x4EA28C`; `MotS AISetMode 0x551670; dispatcher 0x537DD0-0x537E03`; `AI/sithAI.c:429-456`.

Existing source alias: `SITHAI_MODE_UNK100`. Evidence grade: `original-retail-static`.

## jk 0x00000040: Consume-once saber hit-history reset

When the eligible saber collision path sees this bit, it clears the bit and resets the counts of already-hit things and surfaces. The stored histories are pointer lists. The separate saber-damage-enable bit is tested afterward.

**Limits and authoring consequence.** This requests a reset when the path next consumes it; it does not itself enable damage or guarantee another hit. Source puppet marker 0xE sets it, but the original marker dispatch table was not independently reconstructed in this pass.

Evidence anchors: `JK 0x40BBB2-0x40BBDE; list consumers 0x40BD5C,0x40C074,0x40C13E`; `MotS 0x40CED7-0x40CEFD`; `Gameplay/jkSaber.c:368-374; Engine/sithPuppet.c:762-764`.

Existing source alias: `JKFLAG_40`. Evidence grade: `original-retail-static`.

## jk 0x00000100: MotS bubble-owner registration marker

jkCreateBubble registers owner/radius-squared/type in the bubble array and sets this bit on the owner. jkDestroyBubble clears both the record and bit. A query removes a registered record if its owner no longer has the bit.

**Limits and authoring consequence.** This marks the bubble owner, not a thing merely located inside a bubble. Setting the bit alone does not allocate a bubble record or specify radius/type. Use the bubble verbs. An original-JK meaning is not established; lack of bubble verbs is not proof that the bit is universally unused.

Evidence anchors: `MotS jkCreateBubble 0x40C620 calls 0x40F390; set 0x40F41E-0x40F430`; `MotS destroy 0x40F440-0x40F46C; query 0x40F560-0x40F58D`; `Main/jkEpisode.c:709-791`.

Existing source alias: `JKFLAG_100`. Evidence grade: `original-retail-static`.

## multiplayer 0x00000002: Conditional same-team player health-damage suppression

The original actor/player damage paths test multiplayer mode bit 0x2 and return zero before health subtraction when a same-team helper succeeds. That helper also requires teams bit 0x1, distinct player things, non-null player records, and equal nonzero team numbers. The source parent is compared with the victim.

**Limits and authoring consequence.** Self-damage, team zero and unequal teams do not meet this predicate. Earlier COG/inventory callbacks may already have run. This does not promise suppression of all messages, every other damage path or network convergence.

Evidence anchors: `JK 0x4ECFEA-0x4ED014; helper 0x4C9250`; `MotS 0x53B6F3-0x53B71D; helper 0x517890`; `GetMultiModeFlags JK 0x507EE0 / MotS 0x559940; GetPlayerTeam JK 0x4E10F0 / MotS 0x530280`.

Existing source alias: `MULTIMODEFLAG_2`. Evidence grade: `original-retail-static`.

## weapon 0x00010000: Select the special collision/trail update handler

Both original update routines first test weapon 0x2000. Only when it is clear does 0x10000 dispatch to a distinct handler and return. Current source maps that handler to a collision search with optional trail/impact/damage handling and destruction.

**Limits and authoring consequence.** The original proof for both targets is dispatch and priority, not every detail of the reconstructed callee. The full MotS handler was not retraced. The bit alone does not create a trail without the required flags/template/parameters. The old short-throw suggestion is not an established contract.

Evidence anchors: `JK 0x4D3830-0x4D385A, target 0x4D3C20`; `MotS 0x5221F0-0x52221A, target 0x5225F0`; `World/sithWeapon.c:57-84,246-407`.

Existing source alias: `SITH_WF_10000`. Evidence grade: `original-retail-static`.

## face 0x00000010: Original MotS model-face path initially selects lighting mode 1

Original MotS reads model face flags at face+4 and, when 0x10 is set, overrides the initially selected render-entry lighting mode with scalar 1 (source alias NOTLIT). The complete compared JK1.01 model-face routine lacks this override. This proves a lighting consumer beyond the nearest-filter enum label.

**Limits and authoring consequence.** This is an initial mode override in the model-face path. Later ambient/colormap handling can replace mode 1 with mode 0 or 2; no final black/fullbright appearance is established. Nearest filtering, other surface/cache/backend consumers and global JK nonuse are not established. No runtime rendering test.

Evidence anchors: `MotS DrawFace 0x44A620-0x44A9E6 end-exclusive; face flags test 0x44A673, lighting store 0x44A678`; `MotS later ambient/colormap branches 0x44A827-0x44A95F`; `MotS model loader face flags 0x448DFB-0x448E18; model-face caller 0x44A5CB`; `JK DrawFace 0x4467D0-0x446ADF end-exclusive; forwards flags 0x446AA7-0x446AB0 without this override`; `Primitives/rdModel3.c:1713-1724,1731-1733`.

Existing source alias: `RD_FF_TEX_FILTER_NEAREST`. Evidence grade: `original-retail-static`.

## light 0x00000006: Original MotS mode 6 propagates an inherited stored lighting scalar

In original MotS, hierarchy node flag 2 selects mesh lighting mode 6 and copies the stored lighting scalar at mesh+0x44 from the first ancestor without node flag 2. Mode 6 bypasses the ordinary mesh lighting cap and copies that scalar into every face extraLight field at face+0x30. One original producer stores the mean of computed scalar vertex-light outputs in mesh+0x44. The compared JK1.01 hierarchy/mesh routines lack this inheritance, cap exception and mode-6 copy.

**Limits and authoring consequence.** Scalar mode, not a flag bit. Requires a valid ancestor chain and mesh; the original walk lacks the modern null checks. Stored values can be stale, and culling, draw order, face-mode caps and later rendering still matter. It is not proof of fullbright, per-vertex RGB or a dynamic-only value. Current source instead transfers radius at this hierarchy step; original MotS parses and uses radius at mesh+0x48, distinct from the transferred +0x44. No runtime proof.

Evidence anchors: `MotS DrawHNode 0x449F80-0x44A04E; mode write 0x449FB7; ancestor scalar transfer 0x449FD4-0x449FDE`; `MotS mode cap exception 0x44A161-0x44A17F; six-way table 0x44A5FC; mode-6 face copies 0x44A4F9-0x44A50F`; `MotS mean-light producer 0x44A4EA-0x44A4EF, callee 0x4507D0-0x450A3A; sum/divide 0x4509EF-0x450A36`; `MotS radius parser destination 0x4489B6-0x4489C0 and culling read 0x44A0B1`; `JK DrawHNode 0x4462E0-0x44635E; DrawMesh 0x446360-0x4467C8, ordinary cap 0x446452-0x44646C`; `Primitives/rdModel3.c:1453-1461,1533-1547,1629,1646-1652; rdModel3.h:157-178`.

Existing source alias: `RD_LIGHTMODE_6_UNK`. Evidence grade: `original-retail-static`.

## What remains unresolved

ThingFlags `0x20`, `0x01000000`, and `0x40000000` still lack established original-JK/MotS meanings after the additional bounded checks. In particular, Indy's NOSOUND and MOVABLE names are not evidence for those JK/MotS bits. Actor `0x1000`, `0x4000`, and `0x04000000`, plus numerous other family entries, also remain unresolved. Unknown does not mean unused or safe for private script storage.

Weapon `0x10000` has a verified dispatch role in both originals, but the entire MotS callee remains untraced. AI `0x100` has a verified event role; a dedicated persistent-mode behavior remains unproved. Face `0x10` and light mode 6 now have bounded original-MotS paths; whole-renderer behavior, final visual results and other original-JK consumers remain unproved.

## Research method and parity limits

- Current engine-header virtual addresses can point to different functions in JK1.01. Reconcile via registered verbs, pointer fields, call chains and verified bytes; do not assume a uniform delta.
- Named-symbol searches miss literal consumers. Conversely, a matching numeric value in physics, sound, collision, animation or another field does not establish Thing.flags semantics.
- Source symbols are preserved as search aliases, not official historical names or automatic semantic authority.
- Private executable/source/disassembly data is excluded; this supplement contains authored explanations and identities/anchors.

The nearby current weapon damage-decay branch resets damage to minDamage only when the computed value is <=0; the inspected JK1.01 branch compares against minDamage itself. Matching one flag dispatch does not establish whole-function parity.

The newly mapped original-MotS hierarchy transfers stored lighting at mesh+0x44, whereas current source assigns radius. Original radius is parsed and used at +0x48. This source mismatch is recorded without changing the engine.

The private evidence packet retains selected byte receipts and review notes. The public-facing supplement contains no retail scripts, executable payloads, disassembly copies, Discord excerpts, or private local paths. The broad crawl and acquisition goal remain paused.

Original identities:

- jk101: SHA-256 `4509cd690634ba20e132bd16e713f91e144b17e2beaaad5e678f1ddb189b51d9`, 1388544 bytes.
- mots: SHA-256 `23cd064217f904d36d896f52d3cdd17635bb85441a12e0415c0637504191d974`, 1759744 bytes.

The companion `flag-discoveries.json` contains the same 14 findings, target grades, anchors, remaining gaps and current-source hashes. These findings are included in release 0.1.5; the publication receipts separately record deployment and package verification.
