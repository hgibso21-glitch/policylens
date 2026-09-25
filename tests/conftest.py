"""Shared fixtures. Every test gets a fresh in-memory database."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import create_app

WEB_RULESET = {
    "name": "web",
    "address_objects": {"web": ["10.0.1.0/24"]},
    "rules": [
        {
            "name": "https-in",
            "action": "allow",
            "src": ["any"],
            "dst": ["web"],
            "protocol": "tcp",
            "ports": ["443"],
        },
        {"name": "deny-all", "action": "deny", "src": ["any"], "dst": ["any"]},
    ],
}


@pytest.fixture
def engine():
    return db.make_engine("sqlite://")


@pytest.fixture
def client(engine) -> Iterator[TestClient]:
    with TestClient(create_app(engine)) as test_client:  # `with` runs the startup lifespan
        yield test_client


@pytest.fixture
def web_ruleset() -> dict:
    """A valid rule set payload; copy before mutating."""
    return WEB_RULESET
