"""HTTP routes. Business logic stays in engine.py and baseline.py; routes only translate."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app import baseline, engine, reports, repository
from app.db import RuleSetModel
from app.schemas import (
    AuditOut,
    CertificationOut,
    CheckOut,
    FindingOut,
    RuleOut,
    RuleSetIn,
    RuleSetOut,
    RuleSetSummary,
    SummaryOut,
)

router = APIRouter()


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def _get_ruleset_or_404(session: Session, ruleset_id: int) -> RuleSetModel:
    ruleset = session.get(RuleSetModel, ruleset_id)
    if ruleset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"rule set {ruleset_id} not found")
    return ruleset


def _to_out(ruleset: RuleSetModel) -> RuleSetOut:
    return RuleSetOut(
        id=ruleset.id,
        name=ruleset.name,
        address_objects={obj.name: obj.cidrs for obj in ruleset.address_objects},
        rules=[
            RuleOut(
                position=r.position,
                name=r.name,
                action=r.action,
                src=r.src,
                dst=r.dst,
                protocol=r.protocol,
                ports=r.ports,
            )
            for r in ruleset.rules
        ],
    )


# ------------------------------------------------------------------------------ health


@router.get("/healthz", tags=["health"])
def liveness() -> dict[str, str]:
    """Liveness probe: the process is up. Must not touch the database."""
    return {"status": "ok"}


@router.get("/readyz", tags=["health"])
def readiness(session: SessionDep) -> dict[str, str]:
    """Readiness probe: the app can reach its database."""
    session.execute(text("SELECT 1"))
    return {"status": "ready"}


# --------------------------------------------------------------------------- rule sets


@router.post("/rulesets", response_model=RuleSetOut, status_code=status.HTTP_201_CREATED)
def create_ruleset(payload: RuleSetIn, session: SessionDep) -> RuleSetOut:
    try:
        ruleset = repository.create_ruleset(session, payload)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return _to_out(ruleset)


@router.get("/rulesets", response_model=list[RuleSetSummary])
def list_rulesets(session: SessionDep) -> list[RuleSetSummary]:
    rulesets = session.scalars(select(RuleSetModel).order_by(RuleSetModel.id)).all()
    return [RuleSetSummary(id=rs.id, name=rs.name, rule_count=len(rs.rules)) for rs in rulesets]


@router.get("/rulesets/{ruleset_id}", response_model=RuleSetOut)
def get_ruleset(ruleset_id: int, session: SessionDep) -> RuleSetOut:
    return _to_out(_get_ruleset_or_404(session, ruleset_id))


# ---------------------------------------------------------------------------- analysis


@router.get("/rulesets/{ruleset_id}/audit", response_model=AuditOut)
def audit_ruleset(ruleset_id: int, session: SessionDep) -> AuditOut:
    rules = repository.compile_stored(_get_ruleset_or_404(session, ruleset_id))
    findings = [
        FindingOut(
            kind=f.kind,
            severity=f.severity,
            rule_position=f.rule_position,
            rule_name=f.rule_name,
            message=f.message,
            related_position=f.related_position,
        )
        for f in engine.audit(rules)
    ]
    return AuditOut(ruleset_id=ruleset_id, finding_count=len(findings), findings=findings)


@router.get("/rulesets/{ruleset_id}/certification", response_model=CertificationOut)
def certify_ruleset(ruleset_id: int, session: SessionDep) -> CertificationOut:
    rules = repository.compile_stored(_get_ruleset_or_404(session, ruleset_id))
    certified, results = baseline.certify(rules)
    return CertificationOut(
        ruleset_id=ruleset_id,
        certified=certified,
        checks=[
            CheckOut(id=r.check_id, title=r.title, passed=r.passed, details=r.details)
            for r in results
        ],
    )


@router.get("/reports/summary", response_model=SummaryOut)
def summary_report(session: SessionDep) -> SummaryOut:
    return SummaryOut.model_validate({"rulesets": reports.summary(session)})
