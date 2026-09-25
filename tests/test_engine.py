"""Unit tests for the pure rule engine. No database, no HTTP."""

import pytest

from app.engine import (
    RuleSpec,
    audit,
    compile_ruleset,
    covers,
    evaluate,
    find_permissive,
    find_redundant,
    make_query,
)


def rules_from(*specs: RuleSpec, objects: dict | None = None):
    return compile_ruleset(objects or {}, list(specs))


def allow(name="r", src=("any",), dst=("any",), protocol="any", ports=("any",)):
    return RuleSpec(name, "allow", src, dst, protocol, ports)


def deny(name="r", src=("any",), dst=("any",), protocol="any", ports=("any",)):
    return RuleSpec(name, "deny", src, dst, protocol, ports)


class TestCompile:
    def test_resolves_address_objects(self):
        rules = rules_from(
            allow(src=["web"], dst=["10.0.0.0/8"]), objects={"web": ["192.168.1.0/24"]}
        )
        assert [str(n) for n in rules[0].src] == ["192.168.1.0/24"]

    def test_merges_overlapping_ports(self):
        rules = rules_from(allow(protocol="tcp", ports=["80", "81-90", "85"]))
        assert rules[0].ports == ((80, 90),)

    @pytest.mark.parametrize(
        "spec, message",
        [
            (allow(src=["nope"]), "unknown address object"),
            (allow(src=["10.0.0.0/33"]), "not a valid IPv4"),
            (allow(protocol="tcp", ports=["0"]), "out of range"),
            (allow(protocol="tcp", ports=["abc"]), "not a port"),
            (allow(protocol="icmp", ports=["80"]), "only be set for tcp or udp"),
            (RuleSpec("r", "permit", ["any"], ["any"]), "action must be"),
        ],
    )
    def test_rejects_bad_rules(self, spec, message):
        with pytest.raises(ValueError, match=message):
            rules_from(spec)

    def test_rejects_reserved_object_name(self):
        with pytest.raises(ValueError, match="invalid address object name"):
            compile_ruleset({"any": ["10.0.0.0/8"]}, [])


class TestEvaluate:
    def test_first_match_wins(self):
        rules = rules_from(
            deny("block-host", dst=["10.0.0.5/32"]), allow("allow-all", dst=["10.0.0.0/8"])
        )
        decision = evaluate(rules, make_query("1.1.1.1", "10.0.0.5", "tcp", 80))
        assert (decision.action, decision.rule_position) == ("deny", 1)

    def test_no_match_is_implicit_deny(self):
        rules = rules_from(allow(dst=["10.0.0.0/8"], protocol="tcp", ports=["443"]))
        decision = evaluate(rules, make_query("1.1.1.1", "10.0.0.5", "tcp", 22))
        assert decision.action == "deny"
        assert decision.implicit_deny
        assert decision.rule_position is None

    def test_icmp_ignores_port(self):
        rules = rules_from(allow(protocol="icmp"))
        assert evaluate(rules, make_query("1.1.1.1", "2.2.2.2", "icmp", None)).action == "allow"

    @pytest.mark.parametrize(
        "args, message",
        [
            (("nope", "1.1.1.1", "tcp", 1), "invalid IPv4"),
            (("1.1.1.1", "2.2.2.2", "gre", 1), "protocol must be"),
            (("1.1.1.1", "2.2.2.2", "tcp", None), "port is required"),
        ],
    )
    def test_query_validation(self, args, message):
        with pytest.raises(ValueError, match=message):
            make_query(*args)


class TestAudit:
    def test_covers(self):
        broad, narrow = rules_from(allow(dst=["10.0.0.0/8"]), allow(dst=["10.1.0.0/16"]))
        assert covers(broad, narrow)
        assert not covers(narrow, broad)

    def test_duplicate(self):
        findings = find_redundant(
            rules_from(allow("a", dst=["10.0.0.0/8"]), allow("b", dst=["10.0.0.0/8"]))
        )
        assert [(f.kind, f.severity, f.rule_position) for f in findings] == [
            ("duplicate", "low", 2)
        ]

    def test_shadowed_same_action_is_medium(self):
        findings = find_redundant(
            rules_from(allow("a", dst=["10.0.0.0/8"]), allow("b", dst=["10.1.0.0/16"]))
        )
        assert [(f.kind, f.severity) for f in findings] == [("shadowed", "medium")]

    def test_shadowed_opposite_action_is_high(self):
        findings = find_redundant(rules_from(allow("a"), deny("b", dst=["10.1.0.0/16"])))
        assert [(f.kind, f.severity, f.related_position) for f in findings] == [
            ("shadowed", "high", 1)
        ]

    def test_permissive_any_any_is_critical(self):
        findings = find_permissive(rules_from(allow("open")))
        assert [f.severity for f in findings] == ["critical"]

    def test_permissive_any_to_host_is_high(self):
        findings = find_permissive(rules_from(allow("open", dst=["10.0.0.5/32"])))
        assert [f.severity for f in findings] == ["high"]

    def test_restricted_rule_is_not_permissive(self):
        rules = rules_from(allow("https", dst=["10.0.0.5/32"], protocol="tcp", ports=["443"]))
        assert find_permissive(rules) == []

    def test_audit_is_sorted_by_rule_position(self):
        rules = rules_from(allow("open"), deny("late", dst=["10.0.0.0/8"]))
        positions = [f.rule_position for f in audit(rules)]
        assert positions == sorted(positions)
