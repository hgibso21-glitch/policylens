"""Unit tests for baseline certification checks."""

from app.baseline import certify
from app.engine import RuleSpec, compile_ruleset


def compiled(*specs: RuleSpec):
    return compile_ruleset({}, list(specs))


CLEANUP = RuleSpec("deny-all", "deny", ["any"], ["any"])
HTTPS = RuleSpec("https", "allow", ["any"], ["10.0.0.5/32"], "tcp", ["443"])


def failed_ids(rules) -> set[str]:
    _, results = certify(rules)
    return {r.check_id for r in results if not r.passed}


def test_clean_ruleset_is_certified():
    certified, results = certify(compiled(HTTPS, CLEANUP))
    assert certified
    assert all(r.passed for r in results)


def test_any_to_any_allow_fails_bl_001():
    assert "BL-001" in failed_ids(compiled(RuleSpec("open", "allow", ["any"], ["any"]), CLEANUP))


def test_open_ssh_fails_bl_002():
    ssh = RuleSpec("ssh", "allow", ["any"], ["10.0.0.5/32"], "tcp", ["20-25"])
    assert failed_ids(compiled(ssh, CLEANUP)) == {"BL-002"}


def test_missing_cleanup_rule_fails_bl_003():
    assert failed_ids(compiled(HTTPS)) == {"BL-003"}


def test_empty_ruleset_fails_bl_003():
    assert failed_ids([]) == {"BL-003"}


def test_shadowed_rule_fails_bl_004():
    late_deny = RuleSpec("late", "deny", ["any"], ["10.0.0.5/32"], "tcp", ["443"])
    assert failed_ids(compiled(HTTPS, late_deny, CLEANUP)) == {"BL-004"}


def test_duplicate_rule_fails_bl_005():
    assert failed_ids(compiled(HTTPS, HTTPS, CLEANUP)) == {"BL-005"}
