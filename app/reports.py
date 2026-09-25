"""Reporting queries written as raw SQL (the rest of the app uses the ORM)."""

from sqlalchemy import text
from sqlalchemy.orm import Session

RULES_BY_ACTION = text(
    """
    SELECT rs.id AS ruleset_id, rs.name AS ruleset, r.action AS action, COUNT(r.id) AS rules
    FROM rulesets rs
    JOIN rules r ON r.ruleset_id = rs.id
    GROUP BY rs.id, rs.name, r.action
    ORDER BY rs.id, r.action
    """
)

RULES_BY_PROTOCOL = text(
    """
    SELECT rs.id AS ruleset_id, r.protocol AS protocol, COUNT(r.id) AS rules
    FROM rulesets rs
    JOIN rules r ON r.ruleset_id = rs.id
    GROUP BY rs.id, r.protocol
    ORDER BY rs.id, r.protocol
    """
)


def summary(session: Session) -> list[dict]:
    """Rule counts per rule set, grouped by action and by protocol."""
    reports: dict[int, dict] = {}
    for row in session.execute(RULES_BY_ACTION).mappings():
        report = reports.setdefault(
            row["ruleset_id"],
            {
                "ruleset_id": row["ruleset_id"],
                "ruleset": row["ruleset"],
                "by_action": [],
                "by_protocol": [],
            },
        )
        report["by_action"].append({"action": row["action"], "rules": row["rules"]})
    for row in session.execute(RULES_BY_PROTOCOL).mappings():
        reports[row["ruleset_id"]]["by_protocol"].append(
            {"protocol": row["protocol"], "rules": row["rules"]}
        )
    return list(reports.values())
