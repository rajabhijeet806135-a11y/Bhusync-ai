"""
BhuSynch AI — Parcel Vertex Model
===================================
Maps to: Table 2 — parcel_vertices (Section 3 DDL)
Vertex-level error covariance ellipses for uncertainty quantification.
References: Subsystem 4 — Vertex Covariance Error Ellipses Σ = (Σ w A^T A)^(-1)
"""

import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ParcelVertex(Base):
    """
    Individual vertex of a cadastral parcel with error covariance ellipse parameters.

    Each vertex stores:
    - sigma_major_axis_m: Semi-major axis of the positional error ellipse (meters)
    - sigma_minor_axis_m: Semi-minor axis of the positional error ellipse (meters)
    - orientation_deg: Orientation angle of the error ellipse (degrees)
    - confidence_score: Statistical confidence of the vertex position [0.000–1.000]

    The error ellipse is derived from the weighted least-squares covariance matrix:
    Σ = (Σ wₛ Aₛᵀ Aₛ)⁻¹
    where wₛ are source weights and Aₛ are design matrices per data source.
    """

    __tablename__ = "parcel_vertices"

    vertex_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    parcel_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cadastral_parcels.parcel_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vertex_index = Column(Integer, nullable=False)
    sigma_major_axis_m = Column(Numeric(6, 4), nullable=False)
    sigma_minor_axis_m = Column(Numeric(6, 4), nullable=False)
    orientation_deg = Column(Numeric(5, 2), nullable=False)
    confidence_score = Column(Numeric(4, 3), nullable=False)
    geom = Column(
        Geometry(geometry_type="POINT", srid=7755, spatial_index=False),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────────
    parcel = relationship("CadastralParcel", back_populates="vertices")

    # ── Spatial Index (matching Section 3 DDL) ───────────────────────
    __table_args__ = (
        Index("idx_vertices_geom", geom, postgresql_using="gist"),
    )

    def __repr__(self) -> str:
        return (
            f"<ParcelVertex(parcel_id={self.parcel_id!r}, "
            f"idx={self.vertex_index}, σ_maj={self.sigma_major_axis_m})>"
        )
