# Original teaching examples

These six files were written for COG Workshop. They do not contain copied retail or community COG bodies. They use only the native names measured in their declared original-game target. The shared examples use the intersection of the JK 1.01 and MotS registries and source-reviewed call contracts. **Declared target means an authoring target, not a completed retail playtest.**

All examples are single-player level components. No ready-to-play level, multiplayer protocol, third-party art, or retail resource is bundled. See the [human guide](../docs/GUIDE.md) for setup and the [validation record](../docs/EXAMPLE_VALIDATION.md) for checks actually performed.

| File | Target | Ordered editor parameters | Required setup and expected observation |
| --- | --- | --- | --- |
| [shared/cw_counter.cog](shared/cw_counter.cog) | JK 1.01 and MotS | `switchSurface` | Bind an activatable surface. Each activation prints the next integer. A fresh level start resets to zero. |
| [shared/cw_timed_light.cog](shared/cw_timed_light.cog) | JK 1.01 and MotS | `switchSurface`, `litSector`, `offLight`, `onLight`, `holdTime` | Sole controller of that sector's extra light. Activation holds the on value for the interval; repeated activation while busy is ignored. Off means the configured extra-light value, not necessarily a black room. |
| [shared/cw_two_stop.cog](shared/cw_two_stop.cog) | JK 1.01 and MotS | `mover`, `switchSurface`, `moveSpeed` | Path mover with two frames, initially stopped at frame 0. Activations alternate destinations after arrival. A block stops the mover; another activation retries the same destination. |
| [shared/cw_ai_destination.cog](shared/cw_ai_destination.cog) | JK 1.01 and MotS | `switchSurface`, `actor`, `destinationMarker` | Fixed, valid actor and marker; actor has a suitable AI class and navigable geometry. Activation requests a move/look position. Existing AI goals may supersede it. |
| [jk/cw_weapon_index.cog](jk/cw_weapon_index.cog) | JK 1.01 only | `switchSurface` | Prints `GetCurInvWeapon` for the local player. Observe several selected weapons and compare the JK bin definitions. |
| [mots/cw_weapon_index.cog](mots/cw_weapon_index.cog) | MotS only | `switchSurface` | Prints `GetCurInvWeapon2` for the local player. Observe several selected weapons and compare the MotS bin definitions. |

Keep the two `cw_weapon_index.cog` variants in separate game projects: they have the same runtime basename by design. Pick the variant matching the game; do not put both into one mounted package and depend on load order.

Copy one selected file into the test project's `cog` resource directory, add an instance using the editor, and fill parameters in the listed order. Save and build the test episode, then verify that this project actually supplies the loaded file. The editor must make the switch surface usable; declaring a reference alone does not alter its material, geometry or activation flags. For the mover, configure path movement, collision and frame positions in the level/template. This script deliberately contains no crushing damage, automatic return, sound or platform rider policy.

Test one component at a time. A numeric `thing` check against `-1` is only an invalid-sentinel check; it does not detect all stale/recycled references. The AI example assumes persistent level objects and does not support destruction and replacement of the actor or marker. Its intent is to teach a destination request, not supply a complete escort AI.

Each script is offered under the MIT license in [LICENSE](LICENSE). Documentation and research metadata elsewhere in the release may carry different terms; third-party works retain their original ownership.
