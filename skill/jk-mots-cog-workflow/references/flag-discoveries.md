# JKDF2 and MotS: unresolved flag findings

Research dated 2026-10-03 local time, updated 2026-10-04 UTC in **COG Workshop 0.1.6**. This cumulative supplement extends the 0.1.4 audit and 0.1.5 findings; matching main-catalog rows carry the same meanings and limits.

There are **25 bounded flag/value findings with original-executable evidence for at least one target**. This release adds eleven clarifications and expands weapon 0x10000 from dispatch to its complete handler. These are documented behaviors, not a claim of eleven historically novel discoveries or a complete proof of all flag meanings.

Original-static means selected code paths in the exact original JK1.01 and MotS executables checked against their bytes. No game, runtime audio/visual, or connected-client test was performed. Original JK, original MotS and current enhanced source remain separate evidence lanes.

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
| weapon `0x00010000` | Select the range-based collision-query and optional trail handler | Verified code path | Verified code path |
| face `0x00000010` | Original MotS model-face path initially selects lighting mode 1 | Absent from compared routine | Verified code path |
| light `0x00000006` | Original MotS mode 6 propagates an inherited stored lighting scalar | Absent from compared routine | Verified code path |
| jk `0x00000080` | Force maximum saber length on the eligible update branch | Verified code path | Verified code path |
| physics `0x00008000` | Pending bypass of the inspected attached-physics drag application | Verified code path | Verified code path |
| actor `0x02000000` | Skip the target-sector darkness penalty in an AI sight check | Verified code path | Verified code path |
| attach `0x00000001` | Surface attachment discriminator | Verified code path | Verified code path |
| attach `0x00000002` | Thing-face attachment discriminator | Verified code path | Verified code path |
| attach `0x00000004` | Ordinary thing attachment discriminator | Verified code path | Verified code path |
| sound `0x00000001` | Looping attached sound cleanup when its owner is freed | Verified code path | Verified code path |
| sound `0x00000040` | Absolute stored position after a nonlooping sound loses its owner | Verified code path | Verified code path |
| sound `0x00000080` | Followed-owner sound lookup and detachment at owner cleanup | Verified code path | Verified code path |
| weapon `0x00004000` | Distance-based damage reduction in the 0x10000 handler | Verified code path | Verified code path |
| weapon `0x00008000` | Conditional segmented object-trail creation in the 0x10000 handler | Verified code path | Verified code path |

Fields are separate namespaces; light mode 6 is a scalar. Source aliases remain search aids, not recovered original developer names.

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

## weapon 0x00010000: Select the range-based collision-query and optional trail handler

In both original dispatchers, weapon 0x10000 selects this handler after the higher-priority 0x2000 branch. The complete handler traverses returned adjoin crossings and handles the first returned non-adjoin result. Thing hits call damage and can independently attempt force; world hits call surface impact. A non-null impact template enables a creation attempt. The final callee marks the weapon Thing.flags 0x2 for destruction.

**Limits and authoring consequence.** The query uses moveSize as well as range, so this is not established as a zero-width ray. One terminal result is handled; collision ordering and penetration are not established. Destruction is marked, not an immediate storage free. Full downstream helper behavior, successful allocation, visuals and networking remain untested.

Evidence anchors: `JK 0x4D3830-0x4D385A, target 0x4D3C20`; `MotS 0x5221F0-0x52221A, target 0x5225F0`; `World/sithWeapon.c:57-84,246-407`; `Complete bodies: JK 0x4D3C20-0x4D4583; MotS 0x5225F0-0x522F53`; `MotS terminal calls: damage 0x522AAF, force 0x522B12, surface 0x522B31, impact creation 0x522B9F`; `Final mark callees: JK 0x4CCA70-0x4CCA93; MotS 0x51B160-0x51B183`.

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

## jk 0x00000080: Force maximum saber length on the eligible update branch

When neither the extend-4 nor retract-8 branch is selected, bit 0x80 sets saber length to its configured maximum, writes about 0.6 to the source-named timeLeftLengthChange field, clears 4/8 and sets 1. Both original branches retain 0x80; current enhanced source clears it.

**Limits and authoring consequence.** The inspected callers already require JK flag 1 and the routine needs valid player information. Setting 0x80 alone does not enter that caller path. Extend/retract branches take priority. This is not a universal unretractable-saber or runtime appearance claim.

Evidence anchors: `JK length routine 0x40B950-0x40BADB; bit branch 0x40BA77-0x40BA9B; caller 0x40D820-0x40D837`; `MotS length routine 0x40CC60-0x40CDEF; bit branch 0x40CD87-0x40CDAB; caller test 0x40F02B`; `Gameplay/jkSaber.c:179-187`.

Existing source alias: `JKFLAG_SABERFORCEON`. Evidence grade: `original-retail-static`.

## physics 0x00008000: Pending bypass of the inspected attached-physics drag application

The original ApplyForce implementation sets 0x8000 while adding force divided by positive mass to a physics mover velocity, even when the supplied force vector is zero. In the inspected surface/Thing-face attached-physics block, nonzero velocity and nonzero surface drag lead to a bit test: if set, the block clears 0x8000 and skips its linear drag call.

**Limits and authoring consequence.** This is a conditional consumed marker, not permanent friction immunity. If those block prerequisites are not reached it is not consumed there, so a one-frame lifetime is unproved. Setting the bit alone does not apply an impulse. Other drag paths and runtime motion remain untested.

Evidence anchors: `JK ApplyForce wrapper 0x503520; native 0x4F5C20-0x4F5CE1; OR at 0x4F5CCD`; `MotS ApplyForce wrapper 0x554210; native 0x5464F0-0x5465B1; OR at 0x54659D`; `JK dispatcher attachment mask 0x4F5BCA; attached drag test 0x4F7C7A; skipped call 0x4F7D12`; `MotS dispatcher attachment mask 0x54649A; attached drag test 0x5488AD; skipped call 0x548945`; `Engine/sithPhysics.c:222,924-942`.

Existing source alias: `SITH_PF_8000`. Evidence grade: `original-retail-static`.

## actor 0x02000000: Skip the target-sector darkness penalty in an AI sight check

The observer actor bit bypasses the target-sector ambient-light multiplier in the inspected sight-acceptance threshold calculation in both originals. The branch is reached inside the distance and target-light-state gates.

**Limits and authoring consequence.** It does not guarantee detection or sight through geometry. Distance, movement, invisibility, observer blindness, threshold clamping and the final random comparison retain their own effects. Other visibility helpers and runtime probabilities were not established.

Evidence anchors: `JK AI initializer observer binding 0x4E9FC6; complete sight helper 0x4EC3A0-0x4EC58B; bit test 0x4EC450`; `MotS AI initializer observer binding 0x537AC9; complete sight helper 0x53AA60-0x53AC4C; bit test 0x53AB10`; `AI/sithAI.c:245-294,1608-1658`.

Existing source alias: `SITH_AF_SEEINDARK`. Evidence grade: `original-retail-static`.

## attach 0x00000001: Surface attachment discriminator

The native surface attachment setter records its target and writes discriminator 1 into attach_flags. Surface attachment stores a surface; Thing-face stores a parent and face; ordinary Thing attachment maintains parent/child links and a relative position. Detach selects its surface or shared Thing/face branch from this separate field.

**Limits and authoring consequence.** Attachment flags are not Thing.flags: their offsets are JK +0x34 and MotS +0x3C. AttachThingToThingEx ORs its extra mask into this field after ordinary attachment. Arbitrary masks, movement propagation and complete message delivery are unproved; this does not resolve Thing 0x01000000 or attachment 0x8/0x10.

Evidence anchors: `JK discriminator store 0x4CE18B; GetAttachFlags 0x503780; detach 0x4CE660-0x4CE814`; `MotS discriminator store 0x51C8AB; GetAttachFlags 0x5544A0; detach 0x51CD70-0x51CF24`; `Ex OR: JK 0x5038C8-0x5038DD; MotS 0x5545E8-0x5545FD`; `World/sithThing.c:1178-1455; Cog/sithCogFunctionThing.c:971-1039`.

Existing source alias: `SITH_ATTACH_SURFACE`. Evidence grade: `original-retail-static`.

## attach 0x00000002: Thing-face attachment discriminator

The native Thing-face attachment setter records its target and writes discriminator 2 into attach_flags. Surface attachment stores a surface; Thing-face stores a parent and face; ordinary Thing attachment maintains parent/child links and a relative position. Detach selects its surface or shared Thing/face branch from this separate field.

**Limits and authoring consequence.** Attachment flags are not Thing.flags: their offsets are JK +0x34 and MotS +0x3C. AttachThingToThingEx ORs its extra mask into this field after ordinary attachment. Arbitrary masks, movement propagation and complete message delivery are unproved; this does not resolve Thing 0x01000000 or attachment 0x8/0x10.

Evidence anchors: `JK discriminator store 0x4CE37A; GetAttachFlags 0x503780; detach 0x4CE660-0x4CE814`; `MotS discriminator store 0x51CA8A; GetAttachFlags 0x5544A0; detach 0x51CD70-0x51CF24`; `Ex OR: JK 0x5038C8-0x5038DD; MotS 0x5545E8-0x5545FD`; `World/sithThing.c:1178-1455; Cog/sithCogFunctionThing.c:971-1039`.

Existing source alias: `SITH_ATTACH_THINGFACE`. Evidence grade: `original-retail-static`.

## attach 0x00000004: Ordinary thing attachment discriminator

The native ordinary Thing attachment setter records its target and writes discriminator 4 into attach_flags. Surface attachment stores a surface; Thing-face stores a parent and face; ordinary Thing attachment maintains parent/child links and a relative position. Detach selects its surface or shared Thing/face branch from this separate field.

**Limits and authoring consequence.** Attachment flags are not Thing.flags: their offsets are JK +0x34 and MotS +0x3C. AttachThingToThingEx ORs its extra mask into this field after ordinary attachment. Arbitrary masks, movement propagation and complete message delivery are unproved; this does not resolve Thing 0x01000000 or attachment 0x8/0x10.

Evidence anchors: `JK discriminator store 0x4CE5CD; GetAttachFlags 0x503780; detach 0x4CE660-0x4CE814`; `MotS discriminator store 0x51CCDD; GetAttachFlags 0x5544A0; detach 0x51CD70-0x51CF24`; `Ex OR: JK 0x5038C8-0x5038DD; MotS 0x5545E8-0x5545FD`; `World/sithThing.c:1178-1455; Cog/sithCogFunctionThing.c:971-1039`.

Existing source alias: `SITH_ATTACH_THING`. Evidence grade: `original-retail-static`.

## sound 0x00000001: Looping attached sound cleanup when its owner is freed

In the inspected owner-free cleanup, a matching sound with FOLLOWSTHING 0x80 and LOOP 0x1 takes the channel cleanup branch, conditionally stopping active playback and freeing its channel. The matching nonloop branch instead detaches the sound to the last position.

**Limits and authoring consequence.** This adds an original lifecycle consumer of LOOP, not a complete looping/playback contract or an audibility test. The channel must pass owner and follow-state tests. Sound flags are separate from Thing.flags.

Evidence anchors: `JK owner cleanup 0x4DD1B0-0x4DD2C4; FOLLOW test 0x4DD1E0; LOOP test 0x4DD1F1`; `MotS owner cleanup 0x52EBE0-0x52ECF4; FOLLOW test 0x52EC10; LOOP test 0x52EC21`; `Position consumers: JK 0x4DD420-0x4DD595; MotS 0x52EE50-0x52EFC5`; `Devices/sithSoundMixer.c: owner-free and positional-update paths`.

Existing source alias: `SITHSOUNDFLAG_LOOP`. Evidence grade: `original-retail-static`.

## sound 0x00000040: Absolute stored position after a nonlooping sound loses its owner

The matching nonlooping FOLLOWSTHING sound has bit 0x80 cleared and bit 0x40 set during owner-free cleanup, and receives the owner final position. The inspected position update selects the stored position when 0x40 is set.

**Limits and authoring consequence.** This verifies the transition and position selection, not successful playback or audibility. Existing source-based PlaySoundPos behavior is retained in the prior interpretation. It establishes no Thing.flags 0x01000000 meaning.

Evidence anchors: `JK owner cleanup 0x4DD1B0-0x4DD2C4; FOLLOW test 0x4DD1E0; LOOP test 0x4DD1F1`; `MotS owner cleanup 0x52EBE0-0x52ECF4; FOLLOW test 0x52EC10; LOOP test 0x52EC21`; `Position consumers: JK 0x4DD420-0x4DD595; MotS 0x52EE50-0x52EFC5`; `Devices/sithSoundMixer.c: owner-free and positional-update paths`.

Existing source alias: `SITHSOUNDFLAG_ABSOLUTE`. Evidence grade: `original-retail-static`.

## sound 0x00000080: Followed-owner sound lookup and detachment at owner cleanup

Owner-free cleanup selects channels carrying 0x80 whose owner pointer matches the freed Thing. Looping channels enter channel cleanup; nonlooping channels clear 0x80, set absolute-position 0x40 and copy the owner final position.

**Limits and authoring consequence.** This is sound-channel state, not Thing.flags. Other creation and playback gates, networking and runtime audio remain outside this original-static finding.

Evidence anchors: `JK owner cleanup 0x4DD1B0-0x4DD2C4; FOLLOW test 0x4DD1E0; LOOP test 0x4DD1F1`; `MotS owner cleanup 0x52EBE0-0x52ECF4; FOLLOW test 0x52EC10; LOOP test 0x52EC21`; `Position consumers: JK 0x4DD420-0x4DD595; MotS 0x52EE50-0x52EFC5`; `Devices/sithSoundMixer.c: owner-free and positional-update paths`.

Existing source alias: `SITHSOUNDFLAG_FOLLOWSTHING`. Evidence grade: `original-retail-static`.

## weapon 0x00004000: Distance-based damage reduction in the 0x10000 handler

At a terminal collision in the original 0x10000 handler, this bit subtracts rate times hit distance from the local damage amount and floors it at minDamage in both games.

**Limits and authoring consequence.** This updates a local hit amount, not the persistent weapon damage field. Preserve the separately documented ordinary-update decay difference between current source and original JK. Finite-value control flow is established; downstream damage acceptance and runtime outcomes are not.

Evidence anchors: `JK 0x4D408E-0x4D40C7; MotS 0x522A5E-0x522A97`; `Complete handlers: JK 0x4D3C20-0x4D4583; MotS 0x5225F0-0x522F53`; `World/sithWeapon.c:246-407`.

Existing source alias: `SITH_WF_DAMAGE_DECAY`. Evidence grade: `original-retail-static`.

## weapon 0x00008000: Conditional segmented object-trail creation in the 0x10000 handler

The original handler attempts trail-template creation along a locally advanced orientation when bit 0x8000, a trail template and the step/projection versus hit-distance or range gates permit it. The no-hit tail can also create a trail up to range.

**Limits and authoring consequence.** Creation return values are ignored, so allocation and visuals are not proved. The loops have no explicit iteration cap or general progress guard: termination depends on advancing configured step/orientation. This is not a reproduced hang, networking proof or a universal trail contract.

Evidence anchors: `JK complete handler 0x4D3C20-0x4D4583; MotS 0x5225F0-0x522F53`; `MotS first trail loop 0x5226B5-0x522A37; no-hit trail 0x522BC1-0x522F40; creation calls 0x5229DC/0x522EE1`; `World/sithWeapon.c:265-313,362-403`.

Existing source alias: `SITH_WF_OBJECT_TRAIL`. Evidence grade: `original-retail-static`.

## What remains unresolved

Thing `0x20`, `0x01000000`, and `0x40000000` still lack established original-JK/MotS meanings. Sound-owner cleanup and physical attachment did not resolve `0x01000000`; those routines use distinct sound and attachment fields. Do not import Indy NOSOUND/MOVABLE labels or treat unknown bits as safe storage.

Actor `0x1000`, `0x4000`, and `0x04000000` remain unresolved after field-aware checks. Shared actor/weapon union offsets and numeric matches are not actor-consumer proof. Weapon `0x2`, `0x10`, `0x20`, `0x40`, `0x20000`, and `0x100000` were not resolved by the completed handler; nearby collision-result masks belong to another domain. Attachment `0x8` and `0x10` received no new original meaning in this pass.

AI `0x100` retains its verified event role without a proved dedicated persistent-mode behavior. Rendering findings remain bounded to their compared routines; final visual results and other original-JK consumers remain unproved.

## Additional attachment and parity observations

At the inspected attachment call sites, entered-message calls require the child Thing mask `0x80100` to be clear; exited-message calls test `0x100` locally. Downstream dispatch was not fully traced, so this does not guarantee delivered events. Face-attachment landing material checks read parent Thing `0x400000` / `0x800000`, not `0x01000000`.

Both original saber 0x80 branches retain that bit, whereas the compared current source clears it. A modern-source one-shot interpretation must not be silently assigned to the original games. The impulse marker is consumed only when the inspected drag block reaches its test, not necessarily on the next frame.

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

The companion `flag-discoveries.json` contains the same 25 findings, target grades, anchors, remaining gaps and current-source hashes. These findings are included in release 0.1.6; the publication receipts separately record deployment and package verification.
