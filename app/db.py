"""Database models (SQLAlchemy ORM) and engine setup."""

import os

from sqlalchemy import JSON, ForeignKey, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

DEFAULT_DATABASE_URL = "sqlite:///./policylens.db"


def database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def make_engine(url: str) -> Engine:
    if not url.startswith("sqlite"):
        return create_engine(url)
    kwargs: dict = {"connect_args": {"check_same_thread": False}}
    if url in ("sqlite://", "sqlite:///:memory:"):
        kwargs["poolclass"] = StaticPool  # keep one shared in-memory database (used by tests)
    return create_engine(url, **kwargs)


def make_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class RuleSetModel(Base):
    __tablename__ = "rulesets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    address_objects: Mapped[list["AddressObjectModel"]] = relationship(
        back_populates="ruleset", cascade="all, delete-orphan", order_by="AddressObjectModel.id"
    )
    rules: Mapped[list["RuleModel"]] = relationship(
        back_populates="ruleset", cascade="all, delete-orphan", order_by="RuleModel.position"
    )


class AddressObjectModel(Base):
    __tablename__ = "address_objects"

    id: Mapped[int] = mapped_column(primary_key=True)
    ruleset_id: Mapped[int] = mapped_column(ForeignKey("rulesets.id"))
    name: Mapped[str] = mapped_column(String(64))
    cidrs: Mapped[list[str]] = mapped_column(JSON)
    ruleset: Mapped[RuleSetModel] = relationship(back_populates="address_objects")


class RuleModel(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    ruleset_id: Mapped[int] = mapped_column(ForeignKey("rulesets.id"))
    position: Mapped[int]
    name: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(5))
    protocol: Mapped[str] = mapped_column(String(4))
    src: Mapped[list[str]] = mapped_column(JSON)
    dst: Mapped[list[str]] = mapped_column(JSON)
    ports: Mapped[list[str]] = mapped_column(JSON)
    ruleset: Mapped[RuleSetModel] = relationship(back_populates="rules")
