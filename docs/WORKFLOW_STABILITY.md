# Workflow storage and resource validation

Validated on Windows with Python 3.13 on 1 October 2026. These findings apply to the workload safeguards released in version 0.1.1. The original 0.1.0 ZIP was tested as a separate baseline.

## What was tested

The exact 0.1.0 distribution contains 93 ZIP entries and expands to 66,509,608 bytes, about 63.4 MiB. It does not distribute the private research archive. All 68 existing tests passed against that package. A small synthetic repository reproduced a storage defect: its importer accepted an output directory under a `.git` marker and wrote research files there.

The candidate passes all 68 original tests plus 20 new workload regressions (88 total). The regressions check repository and worktree output rejection, junction aliases in both directions, early byte/entry limits, filesystem discovery limits, archive and provenance budgets, partial-result reporting, bounded archive path expansion, and streamed nested members that spill to temporary disk. No Git executable is used to identify a checkout; filesystem markers are sufficient.

Thirteen additional checks use the actual public catalogs and a fresh skill installation: CLI statistics and search; three repeated searches that reach the end of the full catalog without a match; the installed launcher; JK and MotS preflight; local import and exact source lookup for each game; and a local reporter template. All passed. The original release ZIP also passed activation under the candidate's tighter archive limits.

The largest measured Python process peaked at 37.84 MiB during regression runs. The catalog/installed-skill command checks peaked at 24.29 MiB per process; the slowest of those thirteen commands took 0.47 seconds on the test machine. These are observed process peaks and timings, not a total-system RAM bound or a promise for other computers.

## Isolation and limits of the result

Runs were sequential in a temporary data directory outside Git. Child configuration pointed at isolated Codex and managed-data directories. A Python audit hook rejected non-Python child processes, shell commands and external network connections; local loopback connections were permitted for the existing HTTP timeout test. Nothing contacted a live update feed, sent a report, resumed collection or launched Git. The audit harness initially misread Windows' empty executable field in subprocess events; this harness error was corrected before the passing baseline and candidate runs.

These tests address concrete storage and workload failure paths. They do not exercise every Codex desktop build, demonstrate recovery of a previously stalled desktop watcher, prove game runtime behavior, or establish that an unrelated host/application failure cannot occur. Linux and macOS were not rerun for this change. Future releases still need their ordinary package, platform and publication checks.

The reusable regression suite is `tests/test_resource_limits.py`. Bulk imports belong outside Git checkouts and outside installed skills. Normal authoring should use existing metadata or a local search index rather than reacquiring or rebuilding a research collection.
