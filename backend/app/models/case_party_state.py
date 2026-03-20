from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CasePartyStateModel(Base):
    __tablename__ = "case_party_states"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    area: Mapped[str] = mapped_column(String(50), nullable=False)
    state_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "case_id",
            name="uq_case_party_states_tenant_case",
        ),
        Index(
            "ix_case_party_states_case_id_updated_at",
            "case_id",
            "updated_at",
        ),
    )


class CasePartyModel(Base):
    __tablename__ = "case_parties"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    party_state_id: Mapped[int] = mapped_column(
        ForeignKey("case_party_states.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    party_key: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    party_type: Mapped[str] = mapped_column(String(50), nullable=False, default="person")
    document_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    is_original_party: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    party_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "party_state_id",
            "party_key",
            name="uq_case_parties_tenant_state_party_key",
        ),
        Index(
            "ix_case_parties_state_status",
            "party_state_id",
            "status",
        ),
    )


class CasePartyRepresentativeModel(Base):
    __tablename__ = "case_party_representatives"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    party_state_id: Mapped[int] = mapped_column(
        ForeignKey("case_party_states.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    represented_party_key: Mapped[str] = mapped_column(String(100), nullable=False)
    representative_party_key: Mapped[str] = mapped_column(String(100), nullable=False)
    representation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="legal",
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    started_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ended_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    representative_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_case_party_representatives_state_keys",
            "party_state_id",
            "represented_party_key",
            "representative_party_key",
        ),
    )


class CasePartyRelationshipModel(Base):
    __tablename__ = "case_party_relationships"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    party_state_id: Mapped[int] = mapped_column(
        ForeignKey("case_party_states.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_party_key: Mapped[str] = mapped_column(String(100), nullable=False)
    target_party_key: Mapped[str] = mapped_column(String(100), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    started_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ended_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    relationship_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_case_party_relationships_state_type",
            "party_state_id",
            "relationship_type",
        ),
    )


class CasePartyEventModel(Base):
    __tablename__ = "case_party_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    party_state_id: Mapped[int] = mapped_column(
        ForeignKey("case_party_states.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_on: Mapped[str | None] = mapped_column(String(50), nullable=True)
    party_keys: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    event_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_case_party_events_state_created_at",
            "party_state_id",
            "created_at",
        ),
        Index(
            "ix_case_party_events_state_event_type",
            "party_state_id",
            "event_type",
        ),
    )
