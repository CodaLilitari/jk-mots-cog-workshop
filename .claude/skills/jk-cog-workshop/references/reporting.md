# Optional findings reporter

The research destination is **lilitarikiralv@gmail.com**. Reporting is off by default. Using the workshop, searching its corpus, importing local game data, or checking for updates does not send findings, usage logs, local files, or email. The reporter prepares local drafts only. It has no network or email-send implementation, and its CLI commands bypass automatic update checks.

Use a report for a concrete addition or correction that could change the research or an authoring decision. First compare the proposed finding with the current public notes, human guide, compatibility tables, and relevant catalog entries. Record the release reviewed, exact references inspected, searches performed and the difference you found. Keyword searches alone cannot prove novelty; the reporter requires documented comparison but cannot independently establish that a finding is new or correct. A suspected contradiction can still be valuable when its target and evidence limits are clear.

## Prepare a local draft

From this installed skill folder:

```console
python scripts/prepare_finding.py template --out finding.json
```

Fill the JSON template with the finding. It deliberately contains empty required fields and cannot be submitted unchanged. Then prepare new local preview files:

```console
python scripts/prepare_finding.py prepare finding.json --out-prefix finding-review
```

This writes `finding-review.md`, `finding-review.eml`, and `finding-review.review.json`, then prints the exact recipient, subject, body, empty attachment list and content hash. Parent directories must already exist; existing outputs are never overwritten. Revisions need a new output prefix. These commands remain local even without `--offline`. They do not open an email client, activate an installed release, or inspect files other than the exact report path provided. In the full workshop release, the equivalent commands are `python cog_workshop.py report template ...` and `python cog_workshop.py report prepare ...`. The installed helper is self-contained and does not need that release directory.

## Required evidence

| Template section | What to record |
| --- | --- |
| `kind` and `title` | `addition` or `correction`, with one concrete finding per report. |
| `target` | `jk`, `mots` or `enhanced`; exact executable/version or commit, relevant extension version, and `base_game` of `jk` or `mots`. Do not generalize one target's behavior to the other. |
| `research_review` | Workshop release reviewed, references inspected, searches/comparisons performed, and how the finding adds to or contradicts the current research. For a correction, identify the existing claim precisely. |
| `finding.claim` | The proposed factual addition or correction. |
| `finding.expected` and `observed` | What the current claim or baseline predicts, and what was actually observed. |
| `finding.reproduction` | Ordered steps for the smallest useful reproduction; state relevant settings and dependencies. |
| `finding.evidence` | What was inspected or executed. Distinguish lexical checks, parser acceptance, source probes, retail execution and connected-client observations. Refer to public evidence or non-sensitive fixture hashes where useful. |
| `finding.limitations` | Untested targets, inferred mechanisms and unresolved questions. A successful parser check is not retail or multiplayer proof. |
| `finding.proposed_change` | The exact research or authoring recommendation you propose changing. |
| `credit` | Requested contributor credit, or `Anonymous`. A reply address is optional and should be included only if intentionally shared. |
| `public_sources` | Relevant public links or citations; an empty list is permitted when no public source exists. |
| `sharing_review` | What you checked to ensure the report contains only information you intend to share. This statement is not permission for the tool to send it. |

The input limit is 64 KiB. Required fields and list sizes are validated; unsupported fields, duplicate JSON keys and header injection are rejected. **Attachments are not supported in this initial reporter.** Do not paste private conversations, credentials, personal installation paths, owned retail scripts, commercial game files, or third-party payloads into a report. Independently written conclusions and synthetic reproductions can describe a useful observation without disclosing private source material. The reporter does not automatically redact or certify the privacy of text you enter; inspect the exact draft yourself.

## Review and send separately

1. Show the user the **exact recipient, subject, body and attachment list**. The address is `lilitarikiralv@gmail.com`, and this reporter's attachment list is always empty.
2. Obtain an explicit instruction to send that exact report. A request to use the skill or prepare a draft is not an instruction to send it. Each new report or changed payload needs permission covering that version. A content hash identifies the reviewed content but does not grant permission.
3. After that instruction, use an available, authorized email connector or client. If none is connected, provide the `.eml` for the user to open, inspect and send. Do not create accounts, request API keys, or configure SMTP to work around a missing route. Opening an email draft may add the user's sender identity; inspect the final composer before sending.
4. Keep `prepared`, `approved`, `sent`, `delivered` and `accepted` distinct. The helper records only `prepared_not_sent`. A sending route's successful response can establish that the message was sent, but it does not establish recipient delivery, acceptance or incorporation into the research. Preserve a sending reference locally when available; claim delivery only with actual delivery evidence.

There is no test-send feature, automatic crash telemetry, background monitor, mailing-list enrollment, or standing permission for later reports. The maintainer should independently verify useful contributions, respect requested credit, and publish only material cleared for sharing.
