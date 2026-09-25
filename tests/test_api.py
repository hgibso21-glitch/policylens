"""API tests through FastAPI's TestClient (in-memory SQLite, no network)."""

import copy


def create(client, payload) -> dict:
    response = client.post("/rulesets", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


class TestHealth:
    def test_liveness(self, client):
        assert client.get("/healthz").json() == {"status": "ok"}

    def test_readiness_checks_database(self, client):
        assert client.get("/readyz").json() == {"status": "ready"}


class TestRuleSets:
    def test_create_then_get(self, client, web_ruleset):
        created = create(client, web_ruleset)
        assert created["id"] == 1
        assert [r["position"] for r in created["rules"]] == [1, 2]
        assert client.get(f"/rulesets/{created['id']}").json() == created

    def test_list_reports_rule_counts(self, client, web_ruleset):
        create(client, web_ruleset)
        assert client.get("/rulesets").json() == [{"id": 1, "name": "web", "rule_count": 2}]

    def test_get_unknown_returns_404(self, client):
        assert client.get("/rulesets/999").status_code == 404

    def test_unknown_address_object_returns_422(self, client, web_ruleset):
        bad = copy.deepcopy(web_ruleset)
        bad["rules"][0]["dst"] = ["missing_object"]
        response = client.post("/rulesets", json=bad)
        assert response.status_code == 422
        assert "missing_object" in response.json()["detail"]

    def test_schema_validation_returns_422(self, client, web_ruleset):
        bad = {**web_ruleset, "rules": []}
        assert client.post("/rulesets", json=bad).status_code == 422

    def test_invalid_ruleset_is_not_stored(self, client, web_ruleset):
        bad = copy.deepcopy(web_ruleset)
        bad["rules"][0]["src"] = ["999.0.0.0/8"]
        client.post("/rulesets", json=bad)
        assert client.get("/rulesets").json() == []


class TestAnalysis:
    def test_clean_ruleset_has_no_findings_and_is_certified(self, client, web_ruleset):
        create(client, web_ruleset)
        audit = client.get("/rulesets/1/audit").json()
        assert audit == {"ruleset_id": 1, "finding_count": 0, "findings": []}
        certification = client.get("/rulesets/1/certification").json()
        assert certification["certified"] is True
        assert len(certification["checks"]) == 5

    def test_missing_cleanup_rule_is_not_certified(self, client, web_ruleset):
        payload = copy.deepcopy(web_ruleset)
        payload["rules"].pop()
        create(client, payload)
        body = client.get("/rulesets/1/certification").json()
        assert body["certified"] is False
        assert [c["id"] for c in body["checks"] if not c["passed"]] == ["BL-003"]

    def test_audit_and_certification_404(self, client):
        assert client.get("/rulesets/1/audit").status_code == 404
        assert client.get("/rulesets/1/certification").status_code == 404


class TestReports:
    def test_summary_counts_by_action_and_protocol(self, client, web_ruleset):
        create(client, web_ruleset)
        (report,) = client.get("/reports/summary").json()["rulesets"]
        assert report["ruleset"] == "web"
        assert report["by_action"] == [
            {"action": "allow", "rules": 1},
            {"action": "deny", "rules": 1},
        ]
        assert report["by_protocol"] == [
            {"protocol": "any", "rules": 1},
            {"protocol": "tcp", "rules": 1},
        ]

    def test_summary_is_empty_without_data(self, client):
        assert client.get("/reports/summary").json() == {"rulesets": []}
