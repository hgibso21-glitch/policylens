"""FastAPI application entrypoint.  Run locally with:  uvicorn app.main:app --reload"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.engine import Engine

from app import db, seed
from app.routes import router


def create_app(engine: Engine | None = None) -> FastAPI:
    """Build the app. Tests pass their own engine; production reads DATABASE_URL."""
    engine = engine or db.make_engine(db.database_url())
    session_factory = db.make_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        db.Base.metadata.create_all(engine)
        if os.getenv("SEED_MOCK_DATA", "").lower() == "true":
            seed.seed(session_factory)
        yield

    app = FastAPI(
        title="PolicyLens",
        version="0.1.0",
        description="Firewall rule-set analysis: audit, baseline certification and reporting.",
        lifespan=lifespan,
    )
    app.state.session_factory = session_factory
    app.include_router(router)
    return app


app = create_app()
