# Semgrep results

Run #1, `semgrep scan --config p/python --config p/javascript`: 4 findings (2 ERROR, 2 WARNING).

| Planted bug | Caught? | Rule | Severity |
| --- | --- | --- | --- |
| 1. Hardcoded secret | ❌ Missed | — | — |
| 2. SQL injection | ✅ Caught twice | `tainted-sql-string` and `sql-injection-db-cursor-execute` | ERROR + WARNING |
| 3. Command injection (`shell=True`) | ✅ | `subprocess-shell-true` | ERROR |
| 4. `debug=True` | ✅ | `debug-enabled` | WARNING |
| 5. `eval()` in server.js | ❌ Missed | — | — |

## Lessons

- No single tool catches everything: Semgrep missed 2 of 5 planted bugs.
- One SQL finding came from a Django rule on a Flask app. The bug is real, but the fix advice doesn't fit (triage).
- A gate on ERROR only would block SQL injection and command injection, but not `debug=True`.