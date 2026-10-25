# Static capacity validation, 2026-10-25

The original capacity checker was verified with Python 3.13.15 on Windows.
The full `tests` suite passed **90/90 tests**, including 17 capacity test methods.
An independent review exercised 28 additional accounting and malformed-input
controls plus the actual command-line JSON/exit behavior.

```text
python -B -m unittest discover -s tests -v
```

Temporary files and test homes were external to the source checkout. An audit
hook used in the recorded full run blocked external network traffic and
non-Python subprocesses; loopback remained available for the existing timeout
fixture. No game content or downloaded utility ran.

The independent review caught an actual discrepancy: Python's generic line
splitting accepted control characters that the bounded configuration grammar
did not support. The final checker accepts LF/CRLF and reports `unknown` for
unsupported controls, with regression coverage including controls in comments.

Verified checker SHA-256:
`b48e3e3e30f8c36c84eeb014f8045d4cd79b9e9de7e2a2ea57b7086a4a974c54`.

These results establish the declared authored-input accounting and CLI
isolation behavior. They do not establish parser parity, resource loading,
original-game compatibility, savegame correctness or multiplayer behavior.
See [the capacity guide](../docs/STATIC_CAPACITY.md) for the source evidence and
credit to SM Sith Lord's P68 report.
