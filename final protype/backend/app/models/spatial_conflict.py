"""
BhuSynch AI — Spatial Conflict Model
======================================
Maps to: Table 4 — spatial_conflicts (Section 3 DDL)
Three-Truths Conflict Arbitration from Subsystem 4:
  Case A: Area Mismatch (ΔA > 2% Tolerance)
  Case B: Public RoW / Gair Mumkin Intrusion
  Case C: 3D High-Rise Multi-Storey LADM
"""

import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class SpatialConflict(Base):
    """
    Spatial conflict case detected by the Three-Truths Decision Core.

    Three-Truths Matrix:
    - TL (Legal Truth): From RoR/Jamabandi records
    - TP (Physical Truth): From SAM-Geo boundary segmentation + drone imagery
    - TA (Administrative Truth): From government land-use classifications

    Conflict types (Section 2.4):
    - AREA_DISCREPANCY: |legal_area - observed_area| / legal_area > 0.02
    - ROW_ENCROACHMENT: Physical boundary intrudes into Public Right of Way
    - 3D_OVERLAP: Multi-storey building with overlapping floor parcels (LADM)

    Severity levels: LOW, MEDIUM, CRITICAL

    Philosophy: "AI Proposes, Officer Disposes"
    """

    __tablename__ = "spatial_conflicts"

    conflict_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    parcel_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cadastral_parcels.parcel_id"),
        nullable=False,
        index=True,
    )
    conflict_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    discrepancy_area_sqm = Column(Numeric(10, 4), nullable=True)
    disputed_geometry = Column(
        Geometry(geometry_type="GEOMETRY", srid=7755, spatial_index=False),
        nullable=False,
    )
    evidence_payload = Column(JSONB, nullable=False)
    adjudication_status = Column(
        String(30),
        default="PENDING_OFFICER_REVIEW",
        server_default=text("'PENDING_OFFICER_REVIEW'"),
    )
    assigned_officer_id = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # ── Relationships ────────────────────────────────────────────────
    parcel = relationship("CadastralParcel", back_populates="conflicts")

    # ── Spatial Index (matching Section 3 DDL) ───────────────────────
    __table_args__ = (
        Index("idx_conflicts_geom", disputed_geometry, postgresql_using="gist"),
    )

    def __repr__(self) -> str:
        return (
            f"<SpatialConflict(type={self.conflict_type!r}, "
            f"severity={self.severity!r}, status={self.adjudication_status!r})>"
        )
