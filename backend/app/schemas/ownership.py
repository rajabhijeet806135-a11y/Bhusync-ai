"""BhuSynch AI — Ownership Schemas"""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class OwnershipCreate(BaseModel):
    parcel_id: UUID
    owner_name_vernacular: str
    owner_name_english: str
    father_spouse_name: Optional[str] = None
    share_fraction: str = "1/1"
    land_type: Optional[str] = None
    ocr_confidence: Optional[float] = None

class OwnershipResponse(OwnershipCreate):
    record_id: UUID
    model_config = {"from_attributes": True}
