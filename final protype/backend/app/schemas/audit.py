"""BhuSynch AI — Audit Schemas"""
from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel


class AuditEntryResponse(BaseModel):
    entry_id: int
    ulpin: str
    event_type: str
    officer_id: str
    current_hash: str
    prev_merkle_hash: str
    timestamp: Optional[datetime] = None
    model_config = {"from_attributes": True}

class ChainVerificationResponse(BaseModel):
    ulpin: str
    chain_length: int
    is_valid: bool
    broken_at: Optional[int] = None
    chain: list = []
