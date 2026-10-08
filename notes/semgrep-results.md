# Step 3 – Semgrep results

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


# Step 4 – Bandit results

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

# Step 4 – npm audit results

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

# Step 5 – Security gate results

Run #7 "Fail the build on high-severity findings" (commit `dad2a6c`): **Failure**, all three jobs red, exit code 1.

## Design: report step + gate step

Each code robot runs twice: a report step that shows every finding (always green), then a gate step that fails only on serious issues. Developers still see the warnings, but only dangerous issues block them.

| Robot | Gate setting | Blocks on |
| --- | --- | --- |
| Semgrep | `--severity ERROR --error` | ERROR findings |
| Bandit | `-lll` | High severity |
| npm audit | `--audit-level=high` | High or critical |

## What the gate blocks

| Planted bug | Blocks the merge? | Why |
| --- | --- | --- |
| 1. Hardcoded secret | ❌ No, only reported | Bandit rates it Low |
| 2. SQL injection | ✅ Yes | Semgrep ERROR |
| 3. Command injection | ✅ Yes | Semgrep ERROR + Bandit High |
| 4. `debug=True` | ✅ Yes | Bandit High |
| 5. `eval()` | ❌ No | No tool found it |
| 6. Old lodash | ✅ Yes | npm audit High |

## Known limitations

- Hardcoded secrets are reported but not blocked. A dedicated secret scanner (e.g. Gitleaks) that blocks any secret would close this gap.
- `eval()` in server.js was missed by every tool. SAST has blind spots, so manual code review is still needed.
- Blocking only on high severity is a deliberate trade-off to avoid alert fatigue.


# Step 7a – Fixing the vulnerabilities

Branch `fix-vulnerabilities` → Pull Request #1 → merged into `main`.

- PR checks: **all 3 passed** (Semgrep, Bandit, npm audit).
- Run #10 on `main` after the merge: **Success**.
- Before the fixes, run #7 on `main` was **Failure** (all 3 jobs red).

## Fixes

| Bug | Fix | Why it's safe now |
| --- | --- | --- |
| 1. Hardcoded secret | Read `SECRET_KEY` from an environment variable | The secret never ends up in the code or on GitHub |
| 2. SQL injection | Parameterized query with `?` placeholder | The database treats input as data, never as a command |
| 3. Command injection | Argument list without `shell=True`, plus IP address validation | No shell to trick, and non-IP input is rejected |
| 4. Flask `debug=True` | Debug only when `FLASK_DEBUG=1` is set | Off by default |
| 5. `eval()` | `Number()` instead of `eval()` | Input is read as a number, never run as code |
| Old lodash 4.17.15 | Upgraded to 4.18.1 | `npm audit`: 0 vulnerabilities |

## Before vs after

| | Before (run #7) | After (PR #1 / run #10) |
| --- | --- | --- |
| Semgrep gate | ❌ Failed | ✅ Passed |
| Bandit total issues | 5 (2 High) | 3 (0 High) |
| Bandit gate | ❌ Failed | ✅ Passed |
| npm audit | 1 high vulnerability | 0 vulnerabilities |
| Run result | ❌ Failure | ✅ Success |

## Triage

Bandit still reports 3 Low-severity findings, for example B603 ("subprocess call: check for untrusted input").
Reviewed and accepted: no `shell=True` is used, and `ipaddress.ip_address()` rejects any input that isn't an IP address.
Note: Bandit shows "High: 3" under **confidence** (how sure it is), not **severity** (how dangerous). The gate only looks at severity.