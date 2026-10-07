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


# Bandit results

Run: "Updated yaml" (commit `5652b26`), `bandit -r app/python-api --exit-zero`, Bandit 1.9.4.
Bandit found 5 issues: 2 High, 1 Medium, 2 Low.

| Bandit code | What it found | Line | Severity | Confidence |
| --- | --- | --- | --- | --- |
| B404 | `import subprocess` ("be careful with this module") | 3 | Low | High |
| B105 | Hardcoded secret `'super-secret-key-123'` | 10 | Low | Medium |
| B608 | SQL built from a string (SQL injection) | 18 | Medium | Low |
| B602 | `shell=True` (command injection) | 26 | High | High |
| B201 | Flask `debug=True` | 32 | High | Medium |

## Lessons

- Bandit caught the hardcoded secret that Semgrep missed: using more than one tool pays off.
- B404 is noise: importing `subprocess` isn't dangerous by itself, only how it's used. It's close to a false positive.
- The tools disagree on severity: `debug=True` is a WARNING for Semgrep but High for Bandit.
- The secret is only rated Low, so a "block on High only" gate would report it but not block it.

## Scoreboard so far

| Planted bug | Semgrep | Bandit | npm audit |
| --- | --- | --- | --- |
| 1. Hardcoded secret | ❌ Missed | ✅ Low | — |
| 2. SQL injection | ✅ ERROR | ✅ Medium | — |
| 3. Command injection | ✅ ERROR | ✅ High | — |
| 4. `debug=True` | ✅ WARNING | ✅ High | — |
| 5. `eval()` in server.js | ❌ Missed | — (Python only) | — |
| 6. Old lodash 4.17.15 | — | — | To check |

`—` = not this tool's job (Bandit only reads Python; npm audit only checks libraries).

# npm audit results

Run: "updated yaml" (commit `5652b26`), `npm audit || true`, Node 24.21.0, npm 11.19.0.
Result: 1 high severity vulnerability, in lodash.

| Package | Installed | Affected range | Severity | Advisories | Safe version |
| --- | --- | --- | --- | --- | --- |
| lodash | 4.17.15 | <= 4.17.23 | High | 6 (command injection, code injection, prototype pollution x3, ReDoS) | 4.18.1 |

## Lessons

- npm audit doesn't read our code at all. It compares library versions against a database of known vulnerabilities (GHSA / CVE IDs).
- A version that was considered safe (4.17.21) is now vulnerable: new advisories keep being published. Dependency scanning must run on every push, not once.
- The fix is outside the pinned range in package.json, so it's a deliberate upgrade (`npm install lodash@4.18.1`), not an automatic one.

## Final scoreboard (Step 4)

| Planted bug | Semgrep | Bandit | npm audit |
| --- | --- | --- | --- |
| 1. Hardcoded secret | ❌ Missed | ✅ Low | — |
| 2. SQL injection | ✅ ERROR | ✅ Medium | — |
| 3. Command injection | ✅ ERROR | ✅ High | — |
| 4. `debug=True` | ✅ WARNING | ✅ High | — |
| 5. `eval()` in server.js | ❌ Missed | — (Python only) | — |
| 6. Old lodash 4.17.15 | — | — | ✅ High |

`—` = not this tool's job. Only `eval()` was missed by every tool.