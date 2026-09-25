"""Baseline checks used by the certification report.

Each check inspects a compiled rule set and reports pass or fail with details.
A rule set is certified only if every check passes.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from app.engine import FULL_PORTS, Rule, find_redundant, is_any

MANAGEMENT_PORTS = {22: "SSH", 23: "Telnet", 3389: "RDP"}


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    title: str
    passed: bool
    details: list[str] = field(default_factory=list)


def _result(check_id: str, title: str, problems: list[str]) -> CheckResult:
    return CheckResult(check_id, title, passed=not problems, details=problems)


def _exposed_management_ports(rule: Rule) -> list[str]:
    if rule.protocol not in ("tcp", "any"):
        return []
    return [
        label
        for port, label in MANAGEMENT_PORTS.items()
        if any(low <= port <= high for low, high in rule.ports)
    ]


def check_no_any_to_any(rules: Sequence[Rule]) -> CheckResult:
    problems = [
        f"Rule {r.position} ({r.name!r}) allows any source to any destination."
        for r in rules
        if r.action == "allow" and is_any(r.src) and is_any(r.dst)
    ]
    return _result("BL-001", "No allow rule from any source to any destination", problems)


def check_no_open_management(rules: Sequence[Rule]) -> CheckResult:
    problems = []
    for rule in rules:
        if rule.action == "allow" and is_any(rule.src):
            exposed = _exposed_management_ports(rule)
            if exposed:
                labels = ", ".join(exposed)
                problems.append(
                    f"Rule {rule.position} ({rule.name!r}) exposes {labels} to any source."
                )
    return _result("BL-002", "No management ports (SSH, Telnet, RDP) open to any source", problems)


def check_cleanup_rule(rules: Sequence[Rule]) -> CheckResult:
    last = rules[-1] if rules else None
    ok = (
        last is not None
        and last.action == "deny"
        and is_any(last.src)
        and is_any(last.dst)
        and last.protocol == "any"
        and last.ports == FULL_PORTS
    )
    problems = (
        [] if ok else ["The final rule is not an explicit deny from any to any on all services."]
    )
    return _result("BL-003", "Rule set ends with an explicit deny-all cleanup rule", problems)


def check_no_shadowed(rules: Sequence[Rule]) -> CheckResult:
    problems = [
        f"Rule {f.rule_position} ({f.rule_name!r}): {f.message}"
        for f in find_redundant(rules)
        if f.kind == "shadowed"
    ]
    return _result("BL-004", "No shadowed rules", problems)


def check_no_duplicates(rules: Sequence[Rule]) -> CheckResult:
    problems = [
        f"Rule {f.rule_position} ({f.rule_name!r}): {f.message}"
        for f in find_redundant(rules)
        if f.kind == "duplicate"
    ]
    return _result("BL-005", "No duplicate rules", problems)


CHECKS = (
    check_no_any_to_any,
    check_no_open_management,
    check_cleanup_rule,
    check_no_shadowed,
    check_no_duplicates,
)


def certify(rules: Sequence[Rule]) -> tuple[bool, list[CheckResult]]:
    results = [check(rules) for check in CHECKS]
    return all(r.passed for r in results), results
