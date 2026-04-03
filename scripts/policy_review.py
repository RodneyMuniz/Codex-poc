from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from governance.rules import load_policies
from memory.memory_store import get_default_memory_store


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def build_report(repo_root: Path) -> str:
    policies = load_policies()
    logs = _read_jsonl(repo_root / "logs" / "llm_calls.jsonl")
    store = get_default_memory_store(repo_root)
    recent_memories = store.query_memory("policy violation governance misuse", top_k=5)
    claude_path = repo_root / "governance" / "CLAUDE.md"
    claude_present = claude_path.exists()
    violation_count = 0
    for entry in logs:
        payload = json.dumps(entry, ensure_ascii=True).lower()
        for token in policies.get("forbidden_patterns") or []:
            if str(token).strip().lower() in payload:
                violation_count += 1
                break
    lines = [
        "# Weekly Policy Review",
        "",
        f"- Generated: {_utc_now()}",
        f"- CLAUDE.md present: {'yes' if claude_present else 'no'}",
        f"- Logged LLM calls: {len(logs)}",
        f"- Potential policy violations: {violation_count}",
        f"- Recent governance memories sampled: {len(recent_memories)}",
        "",
        "## Active Roles",
        "",
    ]
    for role_name, role_policy in sorted((policies.get("roles") or {}).items()):
        allowed_states = ", ".join(role_policy.get("allowed_states") or [])
        allowed_tools = ", ".join(role_policy.get("tools") or [])
        lines.append(f"- `{role_name}`: states [{allowed_states}] tools [{allowed_tools}]")
    lines.extend(["", "## Recent Memory Signals", ""])
    if not recent_memories:
        lines.append("- No recent memory signals were found.")
    else:
        for item in recent_memories:
            lines.append(f"- [{item['role']}/{item['state']}] {item['message'][:180]}")
    return "\n".join(lines) + "\n"


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    report = build_report(repo_root)
    report_path = repo_root / "governance" / "policy_review_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(report_path)


if __name__ == "__main__":
    main()
