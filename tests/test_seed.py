"""The mock data must always be valid and keep telling the story the docs describe."""

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import create_app
from app.seed import MOCK_RULESETS, seed

EXPECTED_FAILURES = {
    "prod-web-tier": set(),
    "openshift-cluster-egress": {"BL-004"},
    "legacy-dmz": {"BL-001", "BL-002", "BL-003", "BL-004", "BL-005"},
}


def test_seed_is_idempotent(engine):
    factory = db.make_session_factory(engine)
    db.Base.metadata.create_all(engine)
    assert seed(factory) == len(MOCK_RULESETS)
    assert seed(factory) == 0


def test_seed_on_startup_flag(engine, monkeypatch):
    monkeypatch.setenv("SEED_MOCK_DATA", "true")
    with TestClient(create_app(engine)) as client:
        names = [rs["name"] for rs in client.get("/rulesets").json()]
    assert names == list(EXPECTED_FAILURES)


def test_no_seed_by_default(client):
    assert client.get("/rulesets").json() == []


@pytest.mark.parametrize("name, expected", EXPECTED_FAILURES.items())
def test_mock_baseline_outcomes(engine, monkeypatch, name, expected):
    monkeypatch.setenv("SEED_MOCK_DATA", "true")
    with TestClient(create_app(engine)) as client:
        ruleset_id = next(rs["id"] for rs in client.get("/rulesets").json() if rs["name"] == name)
        body = client.get(f"/rulesets/{ruleset_id}/certification").json()
    assert {c["id"] for c in body["checks"] if not c["passed"]} == expected
    assert body["certified"] is (not expected)
