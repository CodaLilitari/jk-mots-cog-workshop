# Independent updater review

Review date: 1 October 2026. This review uses local synthetic release packages, real child processes and one bounded loopback HTTP stream. It performs no public upload and does not claim that the portfolio feed or public packages are reachable. Live publication verification is a separate release step.

**Review status: both reproduced updater issues are repaired. All 33 updater/reviewer tests passed independently on Windows and WSL/Linux against the post-fix files identified below.** Public feed and package reachability remain a separate publication check.

## Baseline reviewed

| File | SHA-256 at initial review |
| --- | --- |
| `tools/workshop.py` | `60337edb2f458cbf529bd86d571f95fe653a33d1398c7d6c46545922aa4889ee` |
| `tests/test_updater.py` | `5f1b165fca72f8dce52b18224c23bce4d78598fd0fea3ef3d80bacb6f5ce01c8` |
| `cog_workshop.py` | `9340997f7022ebdd0632ad2fa50fcb139acfc59019740f557d4b8a3211a256bc` |

All 27 existing updater tests passed independently on Windows. Their useful evidence includes actual subprocess dispatch from an older launcher into a newer managed release; automatic invocation that installs and then dispatches; hash/size rejection; corruption recovery for covered shapes; network failure; process locking; skill-edit preservation; and archive path, link, collision and expansion rejection. Network bytes in the update-flow tests are supplied by local fixtures, not a real public endpoint.

## Counterexamples added by the reviewer

The independent suite is [test_updater_review.py](../tests/test_updater_review.py). Its six test methods include fourteen malformed-metadata subcases and two positive preservation controls.

1. **Wrong JSON type bypassed recovery.** With two managed releases installed, replacing the newer release's `release.json` or `.verified-install.json` with an array, null, string or number raised `AttributeError` at `.get`. The previous verified version was not selected. The equivalent corruption of `skill-install.json` raised `TypeError` instead of returning a preserved-skill result. These are valid JSON inputs of the wrong shape; invalid JSON syntax was already covered by the baseline suite. The skill test additionally requires rejection of non-path `target` values inside an otherwise valid object.
2. **Trickled responses could exceed the intended deadline.** A real loopback `HTTPResponse` sent 40 bytes, one every 0.03 seconds. With a 0.08-second overall budget and 0.25-second socket timeout, `read(65536)` accumulated the response for about 1.20 seconds before the deadline could be checked. The stream did not stall long enough to trigger the socket timeout. This test adapts only the URL authority and isolates real HTTP buffering; it is not an HTTPS test.

Both counterexamples were sent to the updater owner with executable regression tests. The reviewer did not edit the updater implementation.

The implementation now requires local metadata to be JSON objects, validates a registered skill destination as a nonempty absolute path string before choosing any destination, and uses `HTTPResponse.read1` so the deadline is checked between available network reads. The skill-preservation diagnostic reports the actual reason rather than assuming every failure is a local edit. All fourteen malformed-metadata subcases and the real buffering regression pass.

## Final reviewed files and reruns

| File | SHA-256 after fixes |
| --- | --- |
| `tools/workshop.py` | `58cf80a8124b6376c0f7d7c4940bd3dc93269ccce98426fa604c7406f84e1c54` |
| `tests/test_updater.py` | `232d110e25c518ca3279432449788c37842ee70cfe1ca192435f89e744fed1d9` |
| `tests/test_updater_review.py` | `9f604e3a256d53f2808219af62047ac1c21dd147271535d918b1e31bfa50c121` |
| `cog_workshop.py` | `9340997f7022ebdd0632ad2fa50fcb139acfc59019740f557d4b8a3211a256bc` |
| `tools/reporting.py` | `8a72d7b67f53c717bc6f823bcf8dcf28ea91e763e6888f185b3f0d1cdf6e5ddd` |

The combined command `python -B -m unittest discover -s tests -p "test_updater*.py" -v` passed 33 tests on Windows and 33 on WSL/Linux. This count comprises 27 implementation-owner tests and six independent review tests; subcases are not presented as additional top-level tests. The review also inspected the optional reporter integration: `report` is handled before automatic update checks, prepares local previews, and contains no email-send route. Its separate owner tests and any later user-authorized sending are outside these 33 results.

## Preservation controls that already pass

The default skill installation selects `skills/jk-mots-cog-workflow-public` beneath a temporary Codex home and leaves an existing `skills/jk-mots-cog-workflow` tree unchanged. A separate private-corpus sentinel selected through `COG_CORPUS_ROOT` also remains byte-identical. A failed automatic network attempt continues to run the original version and preserves that corpus. These controls use explicit temporary fixtures and compare content hashes.

An initial reviewer test failed to isolate `CODEX_HOME` while testing an empty-list target. That exposed the falsy-default bug by writing a 73-byte synthetic skill fixture to the real public-skill destination. The exact fixture was removed by the updater owner, and the reviewer independently observed that both its file and now-empty directory were absent. Eleven private-skill files matched pre-test export-input hashes; a complete private-tree pre-test baseline was not available, so no whole-tree equality claim is made. The [bounded recovery receipt](review-test-isolation-recovery.json) records those comparisons without exposing local paths. All reviewer cases now isolate the Codex home, workshop home and private-corpus location inside their temporary directory.

## Reviewed design boundaries

- The feed is the update authority. HTTPS origin checks, restricted redirects and the feed's size/SHA-256 constrain accepted package bytes; they are not an independent signing-key system.
- Extraction goes to staging. The original launcher checkout and optional private corpus are not update targets. Managed activation uses a pointer and retains the prior version.
- Existing skill edits are preserved. Installing the public skill is explicit; subsequent managed refreshes require an unchanged recorded tree. The default name does not overwrite the richer private skill.
- Registry inspection is offline lexical preflight. Updating a tool, downloading a package or passing a parser test does not prove a COG works in retail or multiplayer.
- Local integrity metadata is not a security boundary against an attacker who can modify both the application and that metadata.

Run the focused suites with:

```text
python -B -m unittest discover -s tests -p test_updater.py -v
python -B -m unittest discover -s tests -p test_updater_review.py -v
```

Changes to the reviewed files require an appropriately scoped rerun. Keep live-feed verification distinct from these local tests, and do not describe package integrity or automatic dispatch as proof of retail COG behavior.

## Later installed-skill integration

After the independent 33-test review above, installation was extended to register the Workshop launcher in private managed metadata and generate a managed-home pointer in the installed skill. A small `scripts/workshop.py` wrapper delegates to that launcher; it contains no updater implementation of its own. The skill now instructs its user/agent to invoke this entry point before substantive work, honor offline/update opt-out preferences, and reread refreshed guidance. Unavailable or moved launchers produce a recovery diagnostic while the direct offline helpers remain available. See [installation and recovery](UPDATER.md).

The root agent inspected this registration/wrapper delta. The integration author ran eight new isolated tests plus all existing updater, independent reviewer and reporting regressions: **53 tests passed on Windows/Python 3.13.15 and WSL/Linux/Python 3.14.4**. This is a later code inspection and regression result; the earlier independent reviewer did not review this new integration. Its tests cover custom managed homes, real child-process invocation, explicit/environment offline and opt-out controls, daily-check delegation, local report preparation without update checks, new-release registration, private-skill preservation, and moved/copied/malformed installation metadata. Every installation and managed home in these tests is temporary; no public network endpoint or real user skill was used.

| File | SHA-256 after installed-skill integration |
| --- | --- |
| `tools/workshop.py` | `e70bceec4167b5b8a6fe61801ad21530d34abad0015faf237c3927f83e053b16` |
| `skill/jk-mots-cog-workflow/scripts/workshop.py` | `b51486a62e6df2ec38a60e8ad2e593e7e3c933c5b742d6668a5debed05c7d7d2` |
| `tests/test_skill_launcher.py` | `d27541751906ecc67ec37474e2674b40151c4c8d6a6c0aae40b5a748fcc94152` |

Rerun with `python -B -m unittest discover -s tests -p "test_*.py"`. Reading or loading a skill alone does not run Python, and a manually copied skill without installation metadata is not connected to automatic updates. Neither local tests nor this instruction establish that a Codex host has invoked the skill or that the live portfolio feed is available.
