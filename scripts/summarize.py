"""Combine Semgrep, Bandit and npm audit JSON results into one Markdown table.

Usage: python3 scripts/summarize.py <folder with the JSON files>
"""
import json
import sys
from pathlib import Path

FOLDER = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results")
EXPECTED = ["semgrep.json", "bandit.json", "npm-audit.json"]


def load(filename):
    """Read one JSON file. Return None if it's missing or broken."""
    path = FOLDER / filename
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def clean(text):
    """Make text safe inside a Markdown table cell."""
    return " ".join(str(text).split()).replace("|", "\\|")


rows = []

semgrep = load("semgrep.json")
if semgrep:
    for r in semgrep.get("results", []):
        severity = r["extra"].get("severity", "INFO")
        location = r["path"] + ":" + str(r["start"]["line"])
        rule = r["check_id"].split(".")[-1]
        rows.append(("Semgrep", severity, severity == "ERROR", location, rule))

bandit = load("bandit.json")
if bandit:
    for r in bandit.get("results", []):
        severity = r["issue_severity"]
        location = r["filename"] + ":" + str(r["line_number"])
        finding = r["test_id"] + " " + r["issue_text"]
        rows.append(("Bandit", severity, severity == "HIGH", location, finding))

npm = load("npm-audit.json")
if npm:
    for name, vuln in npm.get("vulnerabilities", {}).items():
        severity = vuln["severity"]
        location = "app/node-api: " + name + " " + vuln.get("range", "")
        blocks = severity in ("high", "critical")
        rows.append(("npm audit", severity, blocks, location, "Known vulnerable dependency"))

rows.sort(key=lambda row: not row[2])
blocking = sum(1 for row in rows if row[2])

print("## Security scan summary")
print()
if not rows:
    print("✅ No findings from any tool.")
else:
    print(f"**{len(rows)} findings, {blocking} blocking the merge.**")
    print()
    print("| Tool | Severity | Blocks merge? | Location | Finding |")
    print("| --- | --- | --- | --- | --- |")
    for tool, severity, blocks, location, finding in rows:
        mark = "❌ Yes" if blocks else "No"
        print(f"| {tool} | {severity} | {mark} | `{clean(location)}` | {clean(finding)} |")

missing = [name for name in EXPECTED if load(name) is None]
if missing:
    print()
    print("Note: no results from " + ", ".join(missing) + " (the job may have failed before saving them).")