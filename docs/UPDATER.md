# Portable installation and updates

Requires Python 3.10 or newer, with no third-party Python packages. Extract the release ZIP to a folder you control. Run these commands from that folder:

```console
python cog_workshop.py version
python cog_workshop.py stats
python cog_workshop.py search SetThingVel --limit 12
python cog_workshop.py inspect path/to/candidate.cog --target jk
python cog_workshop.py inspect path/to/candidate.cog --target mots
```

`inspect` is a lexical availability and symbol preflight against measured retail registries. It does not compile the COG or prove engine execution, networking, or retail checksum compatibility. The public catalogs contain metadata and original notes, not owned retail scripts or private Discord messages.

## Automatic update behavior

An ordinary CLI invocation checks the portfolio feed at most once per 24 hours by default. A newer release is downloaded, verified, placed in a separate managed directory, and selected through an atomic pointer. The launcher then runs the active release, including on later invocations of the original launcher. There is no scheduled task, startup service, background daemon, or modification of your working checkout.

The stable authority for updates is:

`https://richard-pemberton-research.darkahn.chatgpt.site/updates/jk-mots-cog-workshop/releases.json`

Explicit commands and controls:

```console
python cog_workshop.py check-update
python cog_workshop.py update
python cog_workshop.py --offline stats
python cog_workshop.py --no-auto-update search checksum
python cog_workshop.py --home path/to/managed-install --offline version
```

Global options go before the command. `--offline` forbids all network requests, including explicit update checks; it still dispatches an already installed newer release. `--no-auto-update` skips only the automatic check. An explicit `check-update`/`update` still checks. The update attempt time is saved even when the network is unavailable so normal offline use does not repeatedly contact the feed. A failed automatic update prints a diagnostic and continues with the existing release.

Environment settings are `COG_WORKSHOP_OFFLINE=1`, `COG_WORKSHOP_AUTO_UPDATE=0`, `COG_WORKSHOP_HOME=<managed directory>` and `COG_WORKSHOP_UPDATE_INTERVAL=<seconds>` (default 86400, minimum 3600). They affect only this tool. No command edits these environment variables or global configuration. `--feed` explicitly changes the trusted feed and requires HTTPS; use it only for an authority you trust.

Default managed location:

- Windows: `%LOCALAPPDATA%\COGWorkshop`.
- Linux and macOS: `$XDG_DATA_HOME/jk-mots-cog-workshop`, or `~/.local/share/jk-mots-cog-workshop` if unset.

The directory contains `versions/<version>/`, `active.json`, the previous active pointer, update timestamps, a process lock, and optional skill installation metadata. It is not the place to store your own levels, COGs, private research, or other work. Releases are immutable managed content; local changes make their integrity check fail and the previous verified release is preferred. Changed directories are preserved rather than silently overwritten. Your original extracted folder is also preserved.

## Install the public Codex skill

```console
python cog_workshop.py --offline install-skill
```

This explicitly opts into maintaining a public skill at `$CODEX_HOME/skills/jk-mots-cog-workflow-public` (default `~/.codex/skills/jk-mots-cog-workflow-public`). It leaves an existing private `jk-mots-cog-workflow` skill intact. The public skill includes its offline metadata catalogs and measured registries. Restart or refresh the host's skill discovery if it does not appear immediately; this command does not control the host app.

The initial install requires a new, nonexistent destination and refuses existing unregistered directories, even empty ones. Later updates replace the installed skill only when its contents still match the recorded installation hashes. A previous skill directory is retained as a timestamped backup inside the sibling `.cog-workshop-backups` container, outside the normal top-level skill entries. User modifications cause the updater to preserve the directory and report that it was skipped. To keep custom edits and install a separate pristine copy, use `install-skill --destination <new-path>`; the new destination becomes the one this installation manages. The updater does not merge skill edits.

From the installed skill directory, `python scripts/workshop.py version` runs the same portfolio updater through the registered launcher. The skill instructs Codex to use that command at the start of substantive work and reread updated instructions. It supports the same `--offline` and `--no-auto-update` controls; no background service runs just because a skill is installed or read. The standalone corpus, inspection, import and finding-draft scripts remain offline. Passing `report` through this wrapper also uses the launcher's local-only reporter path, which bypasses update checks.

Installation generates `.workshop-install.json` inside the installed skill to locate its managed home, including a custom `--home`. The managed `skill-install.json` receipt records the absolute Workshop launcher. These private local paths are generated at installation and are not shipped in the public package. Keep the extracted Workshop directory available until a managed release has replaced its launcher registration. If the registered launcher is moved, removed or unavailable, the wrapper gives a diagnostic without searching unrelated folders or downloading a replacement; the offline helpers still work. Restore that directory, or reconnect an unchanged installation from the new extracted folder using `python cog_workshop.py --home <same-managed-home> --offline install-skill --destination <installed-skill-folder>`. A copied skill directory without installation metadata can use its offline helpers, but has no automatic update connection until installed through the Workshop. Locally edited installations are preserved by the normal hash checks.

## Verification and recovery

The feed must identify this product and a stable numeric version `MAJOR.MINOR.PATCH`; prerelease strings are not accepted. Version comparison is numeric and a normal update cannot downgrade or reinstall the active version. A package must have the exact advertised byte count and SHA-256. These checks authenticate bytes against the HTTPS feed; the initial release does not implement a separate offline signing key.

Feed redirects remain on the same HTTPS origin. The primary ZIP remains on the portfolio origin. Optional mirrors and package redirects are restricted to HTTPS on `github.com`, `gitlab.com`, `release-assets.githubusercontent.com`, or `objects.githubusercontent.com`; URL credentials, fragments, and nonstandard ports are rejected. Only a feed explicitly chosen by the user can change the primary authority.

Limits are a 1 MiB feed, 512 MiB compressed package, 1 GiB expanded package, and 20,000 ZIP entries. Archives cannot contain traversal, absolute paths, alternate data streams, Windows device names, symlinks, special files, encryption, duplicate paths, file/directory conflicts, or case/Unicode collisions. Expansion is bounded and highly compressed large entries are rejected. Feed reads have a 5-second socket timeout and 10-second overall budget; package attempts have a 10-second socket timeout and 120-second overall budget, checked between bounded reads. Up to five declared mirrors may be tried. A stalled read can add up to its socket timeout to an overall budget.

Extraction and verification finish in a fresh staging directory before activation. Replacing `active.json` is atomic on the same filesystem; the previous pointer remains available. If activation fails, the old release remains usable, and a verified orphan version can be reused on retry. The launcher validates per-file hashes in managed versions and can fall back to the previous release if the current pointer or files are damaged. It never deletes a changed managed version. As with any local tool, this is not protection against an attacker who can rewrite both the application and its local integrity metadata. An invalid current and previous release falls back to the original extracted launcher.

An update lock prevents two workshop instances from installing concurrently and is released by the operating system if the process crashes. Windows may keep an in-use skill file locked; a failed replacement restores the previous directory when possible and reports the failure. Retained timestamped backups provide manual recovery after a hard interruption during skill replacement.

## Release feed schema

```json
{
  "schema_version": 1,
  "product": "jk-mots-cog-workshop",
  "latest": {
    "version": "0.1.0",
    "url": "https://richard-pemberton-research.darkahn.chatgpt.site/downloads/jk-mots-cog-workshop-0.1.0.zip",
    "size": 12345,
    "sha256": "replace-with-the-actual-64-character-lowercase-sha256",
    "mirrors": []
  }
}
```

The size and digest above are illustrative, not a usable release. The actual ZIP has `release.json` at its root with `schema_version`, `product`, and `version`, plus `cog_workshop.py`, `tools/workshop.py` and `skill/jk-mots-cog-workflow/SKILL.md`. It has no enclosing version folder. Additional release metadata is permitted. Update activation does not execute install hooks from the ZIP.

The offline tests use locally constructed releases and mocked network delivery, including a real subprocess launching a newer installed release. They do not alone establish that a published portfolio feed or package is reachable; publication verification must retrieve the real feed and compare the real package bytes separately.

```console
python -B -m unittest discover -s tests -p test_updater.py -v
```
