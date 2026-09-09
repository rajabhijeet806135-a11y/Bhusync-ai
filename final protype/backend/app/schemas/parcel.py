"""BhuSynch AI — Parcel Schemas"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ParcelBase(BaseModel):
    state_code: str = Field(..., max_length=2)
    district_code: str = Field(..., max_length=3)
    village_code: str = Field(..., max_length=6)
    khasra_no: str = Field(..., max_length=50)
    khata_no: Optional[str] = Field(None, max_length=50)
    legal_area_sqm: float

class ParcelCreate(ParcelBase):
    geometry_wkt: str

class ParcelResponse(ParcelBase):
    parcel_id: UUID
    ulpin: Optional[str] = None
    observed_area_sqm: Optional[float] = None
    status: str = "PROVISIONAL"
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
