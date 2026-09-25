"""Database access helpers shared by the API routes and the seed script."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import AddressObjectModel, RuleModel, RuleSetModel
from app.engine import Rule, RuleSpec, compile_ruleset
from app.schemas import RuleSetIn


def create_ruleset(session: Session, payload: RuleSetIn) -> RuleSetModel:
    """Validate and store a rule set. Raises ValueError if the rules do not compile."""
    compile_ruleset(payload.address_objects, _specs(payload))
    ruleset = RuleSetModel(
        name=payload.name,
        address_objects=[
            AddressObjectModel(name=name, cidrs=list(cidrs))
            for name, cidrs in payload.address_objects.items()
        ],
        rules=[
            RuleModel(
                position=position,
                name=rule.name,
                action=rule.action,
                protocol=rule.protocol,
                src=list(rule.src),
                dst=list(rule.dst),
                ports=[str(port) for port in rule.ports],
            )
            for position, rule in enumerate(payload.rules, start=1)
        ],
    )
    session.add(ruleset)
    session.commit()
    return ruleset


def find_by_name(session: Session, name: str) -> RuleSetModel | None:
    return session.scalars(select(RuleSetModel).where(RuleSetModel.name == name)).first()


def compile_stored(ruleset: RuleSetModel) -> list[Rule]:
    """Turn a stored rule set back into engine rules."""
    objects = {obj.name: obj.cidrs for obj in ruleset.address_objects}
    specs = [RuleSpec(r.name, r.action, r.src, r.dst, r.protocol, r.ports) for r in ruleset.rules]
    return compile_ruleset(objects, specs)


def _specs(payload: RuleSetIn) -> list[RuleSpec]:
    return [RuleSpec(r.name, r.action, r.src, r.dst, r.protocol, r.ports) for r in payload.rules]
