"""Pydantic request and response models for the API."""

from typing import Literal

from pydantic import BaseModel, Field


class RuleIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    action: Literal["allow", "deny"]
    src: list[str] = Field(min_length=1)
    dst: list[str] = Field(min_length=1)
    protocol: Literal["tcp", "udp", "icmp", "any"] = "any"
    ports: list[str | int] = Field(default_factory=lambda: ["any"])


class RuleSetIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    address_objects: dict[str, list[str]] = Field(default_factory=dict)
    rules: list[RuleIn] = Field(min_length=1)


class RuleOut(BaseModel):
    position: int
    name: str
    action: str
    src: list[str]
    dst: list[str]
    protocol: str
    ports: list[str]


class RuleSetOut(BaseModel):
    id: int
    name: str
    address_objects: dict[str, list[str]]
    rules: list[RuleOut]


class RuleSetSummary(BaseModel):
    id: int
    name: str
    rule_count: int


class QueryOut(BaseModel):
    src: str
    dst: str
    protocol: str
    port: int | None


class DecisionOut(BaseModel):
    action: str
    rule_position: int | None
    rule_name: str | None
    implicit_deny: bool
    explanation: str


class ReachabilityOut(BaseModel):
    ruleset_id: int
    query: QueryOut
    decision: DecisionOut


class FindingOut(BaseModel):
    kind: str
    severity: str
    rule_position: int
    rule_name: str
    message: str
    related_position: int | None


class AuditOut(BaseModel):
    ruleset_id: int
    finding_count: int
    findings: list[FindingOut]


class CheckOut(BaseModel):
    id: str
    title: str
    passed: bool
    details: list[str]


class CertificationOut(BaseModel):
    ruleset_id: int
    certified: bool
    checks: list[CheckOut]


class ActionCount(BaseModel):
    action: str
    rules: int


class ProtocolCount(BaseModel):
    protocol: str
    rules: int


class RuleSetReport(BaseModel):
    ruleset_id: int
    ruleset: str
    by_action: list[ActionCount]
    by_protocol: list[ProtocolCount]


class SummaryOut(BaseModel):
    rulesets: list[RuleSetReport]
