"""
BhuSynch AI — Cadastral Parcel Model
======================================
Maps to: Table 1 — cadastral_parcels (Section 3 DDL)
Base Cadastral Parcels with ULPIN, area measurements, and EPSG:7755 geometry.
"""

import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class CadastralParcel(Base):
    """
    Authoritative cadastral parcel record.

    Fields match Section 3 DDL exactly:
    - parcel_id: UUID primary key
    - ulpin: 14-character Unique Land Parcel Identification Number (Bhu-Aadhaar)
    - state_code, district_code, village_code: Administrative hierarchy
    - khasra_no, khata_no: Revenue record identifiers
    - legal_area_sqm: Area from RoR document (metric m²)
    - observed_area_sqm: Area computed from SAM-Geo boundary segmentation
    - status: PROVISIONAL → CANDIDATE → VERIFIED → ADJUDICATED
    - geom: Polygon geometry in EPSG:7755
    """

    __tablename__ = "cadastral_parcels"

    parcel_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    ulpin = Column(String(14), unique=True, nullable=True, index=True)
    state_code = Column(String(2), nullable=False)
    district_code = Column(String(3), nullable=False)
    village_code = Column(String(6), nullable=False)
    khasra_no = Column(String(50), nullable=False)
    khata_no = Column(String(50), nullable=True)
    legal_area_sqm = Column(Numeric(12, 4), nullable=False)
    observed_area_sqm = Column(Numeric(12, 4), nullable=True)
    status = Column(
        String(30),
        default="PROVISIONAL",
        server_default=text("'PROVISIONAL'"),
        nullable=False,
    )
    geom = Column(
        Geometry(geometry_type="POLYGON", srid=7755, spatial_index=False),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────────────────
    vertices = relationship(
        "ParcelVertex", back_populates="parcel", cascade="all, delete-orphan"
    )
    ownership_records = relationship(
        "RevenueOwnershipRecord", back_populates="parcel", cascade="all, delete-orphan"
    )
    conflicts = relationship(
        "SpatialConflict", back_populates="parcel", cascade="all, delete-orphan"
    )

    # ── Spatial Index (matching Section 3 DDL) ───────────────────────
    __table_args__ = (
        Index("idx_parcels_geom", geom, postgresql_using="gist"),
    )

    def __repr__(self) -> str:
        return (
            f"<CadastralParcel(ulpin={self.ulpin!r}, "
            f"khasra={self.khasra_no!r}, status={self.status!r})>"
        )
