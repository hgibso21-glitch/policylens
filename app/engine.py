"""Pure rule-evaluation logic for PolicyLens.

No web or database code lives here, so every function can be unit tested directly.

Model (deliberately small):
  * IPv4 only.
  * A rule matches on source, destination, protocol and destination port.
  * Rules are evaluated top to bottom; the first match wins.
  * If nothing matches, the traffic is denied (implicit deny).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network

MIN_PORT = 1
MAX_PORT = 65535
FULL_PORTS: tuple[tuple[int, int], ...] = ((MIN_PORT, MAX_PORT),)
PORT_PROTOCOLS = frozenset({"tcp", "udp"})
PROTOCOLS = frozenset({"tcp", "udp", "icmp", "any"})
ACTIONS = frozenset({"allow", "deny"})
OBJECT_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
ANY_NETWORK = IPv4Network("0.0.0.0/0")

PortRange = tuple[int, int]


@dataclass(frozen=True)
class RuleSpec:
    """A rule as a user wrote it: names, CIDRs and port strings, not yet resolved."""

    name: str
    action: str
    src: Sequence[str]
    dst: Sequence[str]
    protocol: str = "any"
    ports: Sequence[str | int] = ("any",)


@dataclass(frozen=True)
class Rule:
    """A rule after object names are resolved and ports are normalised."""

    position: int  # 1-based position in the rule set
    name: str
    action: str
    src: tuple[IPv4Network, ...]
    dst: tuple[IPv4Network, ...]
    protocol: str
    ports: tuple[PortRange, ...]  # merged ranges; FULL_PORTS when not restricted


@dataclass(frozen=True)
class Query:
    src: IPv4Address
    dst: IPv4Address
    protocol: str
    port: int | None


@dataclass(frozen=True)
class Decision:
    action: str
    rule_position: int | None
    rule_name: str | None
    implicit_deny: bool


@dataclass(frozen=True)
class Finding:
    kind: str  # "shadowed" | "duplicate" | "permissive"
    severity: str  # "low" | "medium" | "high" | "critical"
    rule_position: int
    rule_name: str
    message: str
    related_position: int | None = None


# --------------------------------------------------------------------------- parsing


def parse_objects(objects: Mapping[str, Sequence[str]]) -> dict[str, tuple[IPv4Network, ...]]:
    """Validate address objects and turn their CIDR strings into networks."""
    parsed: dict[str, tuple[IPv4Network, ...]] = {}
    for name, cidrs in objects.items():
        if not OBJECT_NAME.match(name) or name.lower() == "any":
            raise ValueError(f"invalid address object name: {name!r}")
        if not cidrs:
            raise ValueError(f"address object {name!r} has no addresses")
        parsed[name] = tuple(_network(cidr, f"address object {name!r}") for cidr in cidrs)
    return parsed


def _network(value: str, context: str) -> IPv4Network:
    try:
        return IPv4Network(value.strip(), strict=False)
    except ValueError as exc:
        raise ValueError(f"{context}: {value!r} is not a valid IPv4 address or CIDR") from exc


def _resolve_networks(
    values: Sequence[str], objects: Mapping[str, tuple[IPv4Network, ...]], rule_name: str
) -> tuple[IPv4Network, ...]:
    networks: list[IPv4Network] = []
    for value in values:
        value = value.strip()
        if value.lower() == "any":
            networks.append(ANY_NETWORK)
        elif value in objects:
            networks.extend(objects[value])
        elif OBJECT_NAME.match(value):
            raise ValueError(f"rule {rule_name!r}: unknown address object {value!r}")
        else:
            networks.append(_network(value, f"rule {rule_name!r}"))
    return tuple(networks)


def _merge_ranges(ranges: Sequence[PortRange]) -> tuple[PortRange, ...]:
    merged: list[list[int]] = []
    for low, high in sorted(ranges):
        if merged and low <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], high)
        else:
            merged.append([low, high])
    return tuple((low, high) for low, high in merged)


def _parse_ports(
    values: Sequence[str | int], protocol: str, rule_name: str
) -> tuple[PortRange, ...]:
    tokens = [str(v).strip().lower() for v in values]
    if not tokens or "any" in tokens:
        return FULL_PORTS
    if protocol not in PORT_PROTOCOLS:
        raise ValueError(f"rule {rule_name!r}: ports can only be set for tcp or udp rules")
    ranges: list[PortRange] = []
    for token in tokens:
        low_text, _, high_text = token.partition("-")
        try:
            low = int(low_text)
            high = int(high_text) if high_text else low
        except ValueError as exc:
            raise ValueError(f"rule {rule_name!r}: {token!r} is not a port or port range") from exc
        if not (MIN_PORT <= low <= high <= MAX_PORT):
            raise ValueError(f"rule {rule_name!r}: port range {token!r} is out of range 1-65535")
        ranges.append((low, high))
    return _merge_ranges(ranges)


def compile_ruleset(objects: Mapping[str, Sequence[str]], specs: Sequence[RuleSpec]) -> list[Rule]:
    """Resolve objects and validate every rule. Raises ValueError on bad input."""
    parsed_objects = parse_objects(objects)
    rules: list[Rule] = []
    for position, spec in enumerate(specs, start=1):
        if spec.action not in ACTIONS:
            raise ValueError(f"rule {spec.name!r}: action must be 'allow' or 'deny'")
        protocol = spec.protocol.lower()
        if protocol not in PROTOCOLS:
            raise ValueError(f"rule {spec.name!r}: protocol must be one of {sorted(PROTOCOLS)}")
        if not spec.src or not spec.dst:
            raise ValueError(f"rule {spec.name!r}: src and dst must not be empty")
        rules.append(
            Rule(
                position=position,
                name=spec.name,
                action=spec.action,
                src=_resolve_networks(spec.src, parsed_objects, spec.name),
                dst=_resolve_networks(spec.dst, parsed_objects, spec.name),
                protocol=protocol,
                ports=_parse_ports(spec.ports, protocol, spec.name),
            )
        )
    return rules


def make_query(src: str, dst: str, protocol: str, port: int | None) -> Query:
    try:
        src_ip = IPv4Address(src)
        dst_ip = IPv4Address(dst)
    except ValueError as exc:
        raise ValueError(f"invalid IPv4 address: {exc}") from exc
    protocol = protocol.lower()
    if protocol not in PROTOCOLS - {"any"}:
        raise ValueError("protocol must be tcp, udp or icmp")
    if protocol in PORT_PROTOCOLS and port is None:
        raise ValueError(f"port is required for {protocol}")
    return Query(src_ip, dst_ip, protocol, port if protocol in PORT_PROTOCOLS else None)


# ------------------------------------------------------------------------ evaluation


def rule_matches(rule: Rule, query: Query) -> bool:
    if rule.protocol not in ("any", query.protocol):
        return False
    if not any(query.src in net for net in rule.src):
        return False
    if not any(query.dst in net for net in rule.dst):
        return False
    if query.port is not None:
        return any(low <= query.port <= high for low, high in rule.ports)
    return True


def evaluate(rules: Sequence[Rule], query: Query) -> Decision:
    """First matching rule decides. No match means implicit deny."""
    for rule in rules:
        if rule_matches(rule, query):
            return Decision(rule.action, rule.position, rule.name, implicit_deny=False)
    return Decision("deny", None, None, implicit_deny=True)


# ---------------------------------------------------------------------------- audit


def _networks_within(inner: Sequence[IPv4Network], outer: Sequence[IPv4Network]) -> bool:
    # Each inner network must sit inside a single outer network. A network covered only by
    # the union of several outer networks is not detected (documented limitation).
    return all(any(i.subnet_of(o) for o in outer) for i in inner)


def _ports_within(inner: Sequence[PortRange], outer: Sequence[PortRange]) -> bool:
    # Ranges are merged, so containment in the union equals containment in one range.
    return all(
        any(o_low <= low and high <= o_high for o_low, o_high in outer) for low, high in inner
    )


def covers(outer: Rule, inner: Rule) -> bool:
    """True if every packet matching `inner` also matches `outer`."""
    return (
        (outer.protocol == "any" or outer.protocol == inner.protocol)
        and _networks_within(inner.src, outer.src)
        and _networks_within(inner.dst, outer.dst)
        and _ports_within(inner.ports, outer.ports)
    )


def find_redundant(rules: Sequence[Rule]) -> list[Finding]:
    """Find rules that can never match because an earlier rule already covers them."""
    findings: list[Finding] = []
    for index, later in enumerate(rules):
        for earlier in rules[:index]:
            if not covers(earlier, later):
                continue
            same_action = earlier.action == later.action
            if same_action and covers(later, earlier):
                kind, severity = "duplicate", "low"
                message = f"Duplicate of rule {earlier.position} ({earlier.name!r})."
            elif same_action:
                kind, severity = "shadowed", "medium"
                message = (
                    f"Never matches: rule {earlier.position} ({earlier.name!r}) already "
                    f"covers it with the same action, so it is redundant."
                )
            else:
                kind, severity = "shadowed", "high"
                message = (
                    f"Never matches: rule {earlier.position} ({earlier.name!r}) covers it "
                    f"with the opposite action ({earlier.action}), so the intent of this "
                    f"rule ({later.action}) is never applied."
                )
            findings.append(
                Finding(kind, severity, later.position, later.name, message, earlier.position)
            )
            break  # report against the first covering rule only
    return findings


def is_any(networks: Sequence[IPv4Network]) -> bool:
    return any(net.prefixlen == 0 for net in networks)


def _all_services(rule: Rule) -> bool:
    return rule.protocol == "any" or (rule.protocol in PORT_PROTOCOLS and rule.ports == FULL_PORTS)


def find_permissive(rules: Sequence[Rule]) -> list[Finding]:
    """Find allow rules that are open to any source on every service."""
    findings: list[Finding] = []
    for rule in rules:
        if rule.action != "allow" or not is_any(rule.src) or not _all_services(rule):
            continue
        if is_any(rule.dst):
            findings.append(
                Finding(
                    "permissive",
                    "critical",
                    rule.position,
                    rule.name,
                    "Allows any source to any destination on every service.",
                )
            )
        else:
            findings.append(
                Finding(
                    "permissive",
                    "high",
                    rule.position,
                    rule.name,
                    "Allows every service from any source to the destination.",
                )
            )
    return findings


def audit(rules: Sequence[Rule]) -> list[Finding]:
    findings = find_redundant(rules) + find_permissive(rules)
    return sorted(findings, key=lambda f: (f.rule_position, f.kind))
