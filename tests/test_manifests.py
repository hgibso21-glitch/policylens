"""Guardrail tests: the OpenShift manifests must keep the security settings AGENTS.md promises."""

import re
from pathlib import Path

import pytest
import yaml

from app.main import app

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = ROOT / "deploy" / "openshift"


def load(name: str) -> dict:
    return yaml.safe_load((MANIFEST_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture
def container() -> dict:
    (container,) = load("deployment.yaml")["spec"]["template"]["spec"]["containers"]
    return container


def test_kustomization_lists_existing_files():
    for resource in load("kustomization.yaml")["resources"]:
        assert (MANIFEST_DIR / resource).is_file(), resource


def test_container_meets_restricted_scc(container):
    security = container["securityContext"]
    assert security["runAsNonRoot"] is True
    assert security["allowPrivilegeEscalation"] is False
    assert security["capabilities"]["drop"] == ["ALL"]
    assert not security.get("privileged", False)
    assert "runAsUser" not in security  # OpenShift assigns the user id


def test_container_has_resource_limits(container):
    assert {"cpu", "memory"} <= set(container["resources"]["limits"])
    assert {"cpu", "memory"} <= set(container["resources"]["requests"])


def test_probes_point_at_real_routes(container):
    paths = set(app.openapi()["paths"])
    assert container["livenessProbe"]["httpGet"]["path"] in paths
    assert container["readinessProbe"]["httpGet"]["path"] in paths


def test_port_matches_dockerfile(container):
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    exposed = int(re.search(r"^EXPOSE (\d+)", dockerfile, re.MULTILINE).group(1))
    assert exposed >= 1024
    assert container["ports"][0]["containerPort"] == exposed
    assert f'"--port", "{exposed}"' in dockerfile


def test_dockerfile_is_not_root():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    users = re.findall(r"^USER (\S+)", dockerfile, re.MULTILINE)
    assert users and users[-1] not in {"root", "0"}


def test_service_and_route_use_the_named_port():
    assert load("service.yaml")["spec"]["ports"][0]["targetPort"] == "http"
    route = load("route.yaml")["spec"]
    assert route["port"]["targetPort"] == "http"
    assert route["tls"]["insecureEdgeTerminationPolicy"] == "Redirect"


def test_configmap_values_are_strings():
    # A bare `true` in YAML is a boolean, which Kubernetes rejects for ConfigMap data.
    assert all(isinstance(v, str) for v in load("configmap.yaml")["data"].values())
