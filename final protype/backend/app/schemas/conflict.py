"""BhuSynch AI — Conflict Schemas"""
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel


class ConflictResponse(BaseModel):
    conflict_id: UUID
    parcel_id: UUID
    conflict_type: str
    severity: str
    discrepancy_area_sqm: Optional[float] = None
    adjudication_status: str = "PENDING_OFFICER_REVIEW"
    assigned_officer_id: Optional[str] = None
    evidence_payload: Dict[str, Any] = {}
    model_config = {"from_attributes": True}
