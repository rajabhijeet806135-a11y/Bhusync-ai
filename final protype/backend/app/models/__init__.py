"""
BhuSynch AI — ORM Models Package
==================================
SQLAlchemy ORM models mapping to PostgreSQL/PostGIS DDL (Section 3).
All spatial columns use SRID 7755 (EPSG:7755 — Indian CRS).
"""

from app.models.cadastral_parcel import CadastralParcel
from app.models.parcel_vertex import ParcelVertex
from app.models.revenue_ownership import RevenueOwnershipRecord
from app.models.spatial_conflict import SpatialConflict
from app.models.audit_ledger import CadastralAuditLedger

__all__ = [
    "CadastralParcel",
    "ParcelVertex",
    "RevenueOwnershipRecord",
    "SpatialConflict",
    "CadastralAuditLedger",
]
