# Updater validation, initial release

Executed 1 October 2026 against the release source. All tests are reproducible, use temporary directories, and do not need an account, token, or private corpus.

| Environment | Command | Result |
| --- | --- | --- |
| Windows, Python 3.13.15 | `python -B -m unittest discover -s tests -p test_updater.py -v` | 27 tests passed |
| WSL Linux, Python 3.14.4 | `python3 -B -m unittest discover -s tests -p test_updater.py -v` | 27 tests passed |

After independent review and fixes, `test_updater*.py` passes **33 tests** on both platforms: the original 27 plus six reviewer tests covering malformed metadata, private-skill separation, network failure fallback and a real loopback trickle-response deadline counterexample. See [the independent review](../docs/UPDATER_REVIEW.md) for the failures found, repairs, final implementation hash and the corrected test-isolation boundary.

The optional findings reporter adds **12 tests**, also passing on Windows and WSL Linux (`python -B -m unittest discover -s tests -p test_reporting.py -v`). These verify required research comparison/evidence, addition/correction and target schemas, local Markdown/EML equivalence, content hashes, header/length/duplicate-key defenses, unsupported attachment/recipient overrides, output preservation and cleanup, and the CLI's lack of update/network/client-launch side effects. Synthetic test reports were prepared locally; no email was sent.

The later installed-skill launcher adds **eight tests** in `test_skill_launcher.py`. The complete `python -B -m unittest discover -s tests -p "test_*.py"` run passed **53 tests** on Windows/Python 3.13.15 and WSL/Linux/Python 3.14.4. The new tests exercise temporary custom-home registration, real wrapper/launcher child processes, offline/opt-out behavior, daily-check delegation, reporter bypass, registration refresh, private-skill preservation, and missing or copied launcher recovery. See the later-integration appendix of the independent review for the changed hashes and the distinct review scope.

The suite exercises numeric version ordering, stable-version validation, feed origin rules, rejected HTTPS downgrades and external redirects, byte-count/digest failures, offline behavior, update intervals, streamed size/deadline bounds, ZIP path/symlink/collision/expansion defenses, concurrent-process locking, source-file preservation, failed activation, retry of a verified orphan, previous-release recovery, explicit skill opt-in, backed-up skill replacement and refusal to overwrite modified or unrelated skill content.

Two tests run the installed fixture launcher in a real child Python process. One verifies that an old source launcher dispatches a newer already managed release; the other traverses the ordinary automatic-update path with mocked network delivery, installs the newer fixture and dispatches it. Fixture versions are 0.0.1, 0.2.0 and 0.3.0. Tests do not download executable code from the internet.

Offline smoke checks also returned release version `0.1.0` and the current public catalog counts: 20,976 COG profile records, 17,723 source records and 586 compatibility records. These are public metadata counts; no private messages or retail source bodies are implied.

This evidence establishes the tested local behavior on Windows and WSL Linux. It does not establish live portfolio availability, a real release upgrade over HTTPS, macOS execution, retail game behavior, or Codex host skill discovery. Published-feed and package checks belong in the final release verification receipt.
