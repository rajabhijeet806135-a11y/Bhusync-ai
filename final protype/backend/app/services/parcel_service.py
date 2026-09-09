"""
BhuSynch AI — Parcel Service
===============================
CRUD operations and spatial queries for cadastral parcels.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from geoalchemy2.functions import ST_AsGeoJSON, ST_Transform, ST_Area
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import structlog

from app.models.cadastral_parcel import CadastralParcel
from app.models.parcel_vertex import ParcelVertex
from app.models.revenue_ownership import RevenueOwnershipRecord

logger = structlog.get_logger(__name__)


class ParcelService:
    """CRUD and spatial query service for cadastral parcels."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_ulpin(self, ulpin: str) -> Optional[CadastralParcel]:
        """Retrieve a parcel by its 14-character ULPIN."""
        stmt = (
            select(CadastralParcel)
            .options(
                selectinload(CadastralParcel.vertices),
                selectinload(CadastralParcel.ownership_records),
                selectinload(CadastralParcel.conflicts),
            )
            .where(CadastralParcel.ulpin == ulpin)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, parcel_id: UUID) -> Optional[CadastralParcel]:
        """Retrieve a parcel by UUID."""
        stmt = (
            select(CadastralParcel)
            .options(
                selectinload(CadastralParcel.vertices),
                selectinload(CadastralParcel.ownership_records),
            )
            .where(CadastralParcel.parcel_id == parcel_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def query_parcels(
        self,
        bbox: Optional[List[float]] = None,
        state_code: Optional[str] = None,
        district_code: Optional[str] = None,
        village_code: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        crs: int = 7755,
    ) -> List[CadastralParcel]:
        """
        Query parcels with spatial and attribute filters.
        Supports OGC Features Part 1 & 2 with CRS filtering.
        """
        stmt = select(CadastralParcel)

        if bbox and len(bbox) == 4:
            minx, miny, maxx, maxy = bbox
            envelope = text(
                f"ST_MakeEnvelope({minx}, {miny}, {maxx}, {maxy}, {crs})"
            )
            stmt = stmt.where(
                func.ST_Intersects(CadastralParcel.geom, envelope)
            )

        if state_code:
            stmt = stmt.where(CadastralParcel.state_code == state_code)
        if district_code:
            stmt = stmt.where(CadastralParcel.district_code == district_code)
        if village_code:
            stmt = stmt.where(CadastralParcel.village_code == village_code)
        if status:
            stmt = stmt.where(CadastralParcel.status == status)

        stmt = stmt.order_by(CadastralParcel.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_parcel(self, parcel_data: Dict[str, Any]) -> CadastralParcel:
        """Create a new cadastral parcel."""
        parcel = CadastralParcel(**parcel_data)
        self.db.add(parcel)
        await self.db.flush()
        logger.info("parcel_created", parcel_id=str(parcel.parcel_id))
        return parcel

    async def update_status(self, parcel_id: UUID, new_status: str) -> CadastralParcel:
        """Update parcel status (PROVISIONAL → CANDIDATE → VERIFIED → ADJUDICATED)."""
        stmt = select(CadastralParcel).where(CadastralParcel.parcel_id == parcel_id)
        result = await self.db.execute(stmt)
        parcel = result.scalar_one()
        parcel.status = new_status
        await self.db.flush()
        return parcel

    async def count_parcels(self, **filters) -> int:
        """Count total parcels matching filters."""
        stmt = select(func.count(CadastralParcel.parcel_id))
        if "state_code" in filters:
            stmt = stmt.where(CadastralParcel.state_code == filters["state_code"])
        result = await self.db.execute(stmt)
        return result.scalar()
