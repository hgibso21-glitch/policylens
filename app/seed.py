"""Mock data so the API has something to analyse without a real firewall or cluster.

Three rule sets, chosen so each baseline outcome is represented:

  * prod-web-tier            - clean, passes every baseline check
  * openshift-cluster-egress - one flaw: an allow rule added after a deny that shadows it
  * legacy-dmz               - many flaws: open SSH, any-to-any, duplicates, no cleanup rule

The cluster egress set uses OpenShift's default pod (10.128.0.0/14) and service
(172.30.0.0/16) networks; the other addresses are reserved documentation ranges.

Run once from the command line:  python -m app.seed
The API also calls seed() on startup when SEED_MOCK_DATA=true.
"""

from sqlalchemy.orm import Session, sessionmaker

from app import db, repository
from app.schemas import RuleSetIn

MOCK_RULESETS: list[dict] = [
    {
        "name": "prod-web-tier",
        "address_objects": {
            "web_servers": ["10.10.1.0/24"],
            "app_servers": ["10.10.2.0/24"],
            "db_servers": ["10.10.3.0/24"],
            "admin_net": ["10.99.0.0/24"],
        },
        "rules": [
            {
                "name": "https-in",
                "action": "allow",
                "src": ["any"],
                "dst": ["web_servers"],
                "protocol": "tcp",
                "ports": ["443"],
            },
            {
                "name": "web-to-app",
                "action": "allow",
                "src": ["web_servers"],
                "dst": ["app_servers"],
                "protocol": "tcp",
                "ports": ["8080"],
            },
            {
                "name": "app-to-db",
                "action": "allow",
                "src": ["app_servers"],
                "dst": ["db_servers"],
                "protocol": "tcp",
                "ports": ["5432"],
            },
            {
                "name": "admin-ssh",
                "action": "allow",
                "src": ["admin_net"],
                "dst": ["web_servers", "app_servers", "db_servers"],
                "protocol": "tcp",
                "ports": ["22"],
            },
            {"name": "deny-all", "action": "deny", "src": ["any"], "dst": ["any"]},
        ],
    },
    {
        "name": "openshift-cluster-egress",
        "address_objects": {
            "pod_network": ["10.128.0.0/14"],
            "service_network": ["172.30.0.0/16"],
            "registry": ["198.51.100.10/32"],
            "corp_dns": ["192.0.2.53/32"],
            "mirror": ["198.51.100.20/32"],
        },
        "rules": [
            {
                "name": "pods-to-dns",
                "action": "allow",
                "src": ["pod_network"],
                "dst": ["corp_dns"],
                "protocol": "udp",
                "ports": ["53"],
            },
            {
                "name": "pods-to-registry",
                "action": "allow",
                "src": ["pod_network"],
                "dst": ["registry"],
                "protocol": "tcp",
                "ports": ["443"],
            },
            {
                "name": "pods-to-services",
                "action": "allow",
                "src": ["pod_network"],
                "dst": ["service_network"],
                "protocol": "tcp",
            },
            {
                "name": "block-pod-internet",
                "action": "deny",
                "src": ["pod_network"],
                "dst": ["any"],
            },
            {
                "name": "pods-to-mirror",
                "action": "allow",
                "src": ["pod_network"],
                "dst": ["mirror"],
                "protocol": "tcp",
                "ports": ["443"],
            },
            {"name": "deny-all", "action": "deny", "src": ["any"], "dst": ["any"]},
        ],
    },
    {
        "name": "legacy-dmz",
        "address_objects": {"dmz_hosts": ["203.0.113.0/28"]},
        "rules": [
            {
                "name": "ssh-from-anywhere",
                "action": "allow",
                "src": ["any"],
                "dst": ["dmz_hosts"],
                "protocol": "tcp",
                "ports": ["22"],
            },
            {
                "name": "web",
                "action": "allow",
                "src": ["any"],
                "dst": ["dmz_hosts"],
                "protocol": "tcp",
                "ports": ["80", "443"],
            },
            {
                "name": "web-tls-only",
                "action": "allow",
                "src": ["any"],
                "dst": ["dmz_hosts"],
                "protocol": "tcp",
                "ports": ["443"],
            },
            {
                "name": "web-again",
                "action": "allow",
                "src": ["any"],
                "dst": ["dmz_hosts"],
                "protocol": "tcp",
                "ports": ["80", "443"],
            },
            {"name": "temporary-allow-all", "action": "allow", "src": ["any"], "dst": ["any"]},
            {
                "name": "block-rdp",
                "action": "deny",
                "src": ["any"],
                "dst": ["dmz_hosts"],
                "protocol": "tcp",
                "ports": ["3389"],
            },
        ],
    },
]


def seed(session_factory: sessionmaker[Session]) -> int:
    """Insert any mock rule sets that are not already stored. Returns how many were added."""
    added = 0
    with session_factory() as session:
        for data in MOCK_RULESETS:
            if repository.find_by_name(session, data["name"]) is None:
                repository.create_ruleset(session, RuleSetIn.model_validate(data))
                added += 1
    return added


if __name__ == "__main__":
    engine = db.make_engine(db.database_url())
    db.Base.metadata.create_all(engine)
    print(f"Seeded {seed(db.make_session_factory(engine))} rule set(s) into {db.database_url()}")
