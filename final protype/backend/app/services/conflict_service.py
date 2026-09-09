"""
BhuSynch AI — Conflict Service
=================================
Three-Truths Conflict Arbitration logic (Subsystem 4).
"AI Proposes, Officer Disposes"
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from app.models.cadastral_parcel import CadastralParcel
from app.models.spatial_conflict import SpatialConflict

logger = structlog.get_logger(__name__)

# Area discrepancy tolerance (Section 2.4)
AREA_TOLERANCE = Decimal("0.02")  # 2%


class ConflictService:
    """
    Three-Truths Conflict Detection and Management.

    Cases (Section 2.4):
    A: Area Mismatch — ΔA > 2% tolerance
    B: Public RoW / Gair Mumkin Intrusion
    C: 3D High-Rise Multi-Storey LADM
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_area_discrepancy(self, parcel_id: UUID) -> Optional[Dict]:
        """
        Case A: Check if observed area deviates > 2% from legal area.
        |legal_area - observed_area| / legal_area > 0.02
        """
        stmt = select(CadastralParcel).where(CadastralParcel.parcel_id == parcel_id)
        result = await self.db.execute(stmt)
        parcel = result.scalar_one_or_none()

        if not parcel or not parcel.observed_area_sqm:
            return None

        legal = parcel.legal_area_sqm
        observed = parcel.observed_area_sqm
        delta = abs(legal - observed) / legal

        if delta > AREA_TOLERANCE:
            severity = "CRITICAL" if delta > Decimal("0.10") else "MEDIUM" if delta > Decimal("0.05") else "LOW"
            discrepancy = float(abs(legal - observed))

            return {
                "conflict_type": "AREA_DISCREPANCY",
                "severity": severity,
                "discrepancy_area_sqm": discrepancy,
                "delta_percentage": float(delta * 100),
                "legal_area": float(legal),
                "observed_area": float(observed),
            }

        return None

    async def create_conflict(
        self,
        parcel_id: UUID,
        conflict_type: str,
        severity: str,
        disputed_geometry_wkt: str,
        evidence: Dict[str, Any],
        discrepancy_area: Optional[float] = None,
    ) -> SpatialConflict:
        """Create a new spatial conflict case."""
        from geoalchemy2.functions import ST_GeomFromText

        conflict = SpatialConflict(
            parcel_id=parcel_id,
            conflict_type=conflict_type,
            severity=severity,
            discrepancy_area_sqm=discrepancy_area,
            disputed_geometry=ST_GeomFromText(disputed_geometry_wkt, 7755),
            evidence_payload=evidence,
        )

        self.db.add(conflict)
        await self.db.flush()

        logger.info(
            "conflict_created",
            conflict_id=str(conflict.conflict_id),
            type=conflict_type,
            severity=severity,
        )

        return conflict

    async def get_conflicts_for_parcel(self, parcel_id: UUID) -> List[SpatialConflict]:
        """Retrieve all conflicts for a parcel."""
        stmt = (
            select(SpatialConflict)
            .where(SpatialConflict.parcel_id == parcel_id)
            .order_by(SpatialConflict.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def adjudicate_conflict(
        self,
        conflict_id: UUID,
        officer_id: str,
        decision: str,
    ) -> SpatialConflict:
        """
        Officer adjudication of a conflict case.
        "AI Proposes, Officer Disposes"
        """
        stmt = select(SpatialConflict).where(SpatialConflict.conflict_id == conflict_id)
        result = await self.db.execute(stmt)
        conflict = result.scalar_one_or_none()

        if not conflict:
            raise ValueError(f"Conflict {conflict_id} not found")

        conflict.adjudication_status = decision
        conflict.assigned_officer_id = officer_id

        await self.db.flush()

        logger.info(
            "conflict_adjudicated",
            conflict_id=str(conflict_id),
            officer=officer_id,
            decision=decision,
        )

        return conflict
