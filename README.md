# JK / MotS COG Workshop

Write, understand, debug and port COG scripts for **Jedi Knight: Dark Forces II**
and **Mysteries of the Sith**, using a human guide, a reusable Codex skill,
measured compatibility tables and a source-backed research catalog.

**Current release: 0.1.1.** The public edition contains authored research notes,
metadata, original examples and tools. Original game files and private source
archives remain local. Read [the distribution notice](NOTICE.md) for the exact
boundary and [the corpus guide](corpus/README.md) for public coverage.

| Start here | What it gives you |
| --- | --- |
| [Human COG-writing guide](docs/GUIDE.md) | A practical path from symbols and messages to complete game systems |
| [JKDF2 versus MotS](docs/COMPATIBILITY.md) | Stock-game differences, shared names with different contracts, and extension boundaries |
| [Original examples](examples/README.md) | Small teaching components with explicit targets and validation limits |
| [Machine workflow](skill/jk-mots-cog-workflow/SKILL.md) | Retrieval, authoring, debugging and validation guidance for Codex |
| [Research corpus](corpus/README.md) | Reviewed notes, public-source records and exact COG identities |
| [Optional discovery reporter](docs/REPORTING.md) | Reviewed evidence for an addition or correction, prepared as a local email draft |

## Download and use

Download the release ZIP from the [portfolio project page](https://richard-pemberton-research.darkahn.chatgpt.site/projects/jk-mots-cog-workshop/index.html)
or either [GitLab](https://gitlab.com/codalilitari/jk-mots-cog-workshop/-/releases)
or [GitHub](https://github.com/CodaLilitari/jk-mots-cog-workshop/releases), and
extract it into a new folder. Python 3.10 or newer is required for the tools;
the guides can be read without Python. The runtime tools use Python's standard
library.

Keep private research imports and bulk downloads outside Git repositories and outside the installed skill. Use a separate user data directory; the importer and managed updater reject output inside Git checkouts. Routine COG work uses the bundled catalog or an existing local index and does not require crawling or rebuilding a corpus.

See [workflow resource validation](docs/WORKFLOW_STABILITY.md) for the tested safeguards and their limits.

From the extracted folder:

```text
python cog_workshop.py --offline stats
python cog_workshop.py --offline search "SendTrigger" --limit 10
python cog_workshop.py --offline inspect path/to/your.cog --target jk
python cog_workshop.py --offline inspect path/to/your.cog --target mots
```

`inspect` checks lexical call and message availability against measured original
registrations. It is not a compiler and does not run the game. Search results
identify evidence to read; a matching name does not establish working code.

## Install the Codex skill

```text
python cog_workshop.py install-skill
```

The public skill is installed as **`jk-mots-cog-workflow-public`**, separately
from an existing private `jk-mots-cog-workflow`. The installer preserves
unrelated or locally modified content. Reopen or refresh your Codex session
if the new skill is not yet listed. You can then ask Codex to use the public
skill to implement a behavior for a named target game.

For a good request, specify the target, the script's role, its inputs and its
expected lifecycle. For example: “Use the COG workflow to make a stock MotS
single-player switch open a two-frame door; repeated activation while moving
must not restart it, and explain the required level parameters.”

## Portfolio-based automatic updates

Normal workshop invocations check the fixed
[portfolio release feed](https://richard-pemberton-research.darkahn.chatgpt.site/updates/jk-mots-cog-workshop/releases.json)
at a bounded interval. New packages are verified by their declared size and
SHA-256 before installation into a separate managed directory. Your source
checkout, authored COGs and optional private corpus are not replaced.

```text
python cog_workshop.py check-update
python cog_workshop.py update
python cog_workshop.py --offline stats
```

Use `--offline` to prevent network access, or `--no-auto-update` to skip the
automatic check for one invocation. Read [the updater guide](docs/UPDATER.md)
for installation locations, active-version behavior, managed skill updates,
recovery and trust boundaries. This mechanism distributes published releases;
it does not restart the research crawler or upload local material.

## Choose the game before writing the script

- **Stock JKDF2 1.01:** use its measured verb and message tables, native argument
  contracts and corresponding retail examples.
- **Stock MotS:** use the MotS tables and integration conventions. Weapon
  numbering, Force behavior and some identically named calls differ from JK.
- **Enhanced engines and cogext:** identify the exact build or extension.
  Additional registrations in an enhanced JK mode do not prove stock JK support.

The human guide and skill label these cases explicitly. A script parsing in
one engine does not establish that its resources, messages, network behavior
or multiplayer checksum are correct in another.

## Contribute a discovery or correction

Reporting is optional and off by default. If a new implementation or experiment
adds to or contradicts the research, compare it with the current corpus first.
Record the exact game/build, existing claim, reproducible observation, supporting
evidence and remaining limits. The [reporter](docs/REPORTING.md) prepares a local
email draft for **lilitarikiralv@gmail.com** and shows its exact content for review.
It does not send email, upload source files, or collect telemetry. A user may
then explicitly approve and send that particular report through an available
email client or connected email tool. A proposed finding remains unconfirmed
until it has been independently checked.

```text
python cog_workshop.py report template --out finding.json
python cog_workshop.py report prepare finding.json --out-prefix reviewed-finding
```

Complete the template between these commands. Preparation produces a readable
Markdown preview, an `.eml` draft and a review receipt. Report commands perform
no automatic update check or network operation.

## Evidence and scope

The underlying local research snapshot examined 25,364 exact COG body hashes
across 70,346 package occurrences, including the owned retail sets, public
community archives and privately retained material. Those are research-snapshot
counts, **not counts of script bodies distributed in this release**. The public
corpus reports its own filtered metadata and note counts separately.

The workshop preserves original attribution, distinguishes unchanged stock
members from a package author's work, and records unresolved historical and
compatibility questions. It separates source inspection, adapted parser
checks, original-executable evidence, bounded implementation probes and actual
game/network tests. Initial-release examples have their own validation record;
there is no blanket claim of retail or multiplayer execution.

## Develop or publish an update

Run the included tests, review the public export and build the deterministic
package with `python tools/build_release.py`. Release generation uses an
allowlist and scans for private-data markers; editorial review is also required.
Versioned packages belong on the portfolio and both forge releases. Update
the portfolio feed only after the exact new package is available.

The original workshop code, examples and authored documentation use the
[MIT license](LICENSE). Cataloged third-party works retain their own rights.
Direction: Andrei Pemberton. Research and engineering collaboration: Coda
Lilitari through Codex. See [NOTICE.md](NOTICE.md) for attribution boundaries.
