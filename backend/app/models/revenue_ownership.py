"""
BhuSynch AI — Revenue Ownership Record Model
==============================================
Maps to: Table 3 — revenue_ownership_records (Section 3 DDL)
Legal RoR Ownership Registry from Subsystem 2 (Document AI + ULPIN).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class RevenueOwnershipRecord(Base):
    """
    Legal ownership record extracted from scanned RoR/Jamabandi documents.

    Extraction pipeline (Section 2.2):
    [Scanned RoR] → [LayoutLMv3] → [TrOCR Indic] → [Sarvam-1 LLM] → [Entity Tuples]

    Fields:
    - owner_name_vernacular: Name in original Indic script (Hindi/Marathi/Telugu/etc.)
    - owner_name_english: Transliterated English name via canonical identity vector
    - share_fraction: Ownership share (e.g., '1/3', '1/1')
    - land_type: Classification — Khari, Bagayat, Gair Mumkin
    - ocr_confidence: TrOCR recognition confidence [0.000–1.000]
    - raw_document_url: MinIO S3 URL to the scanned source document
    """

    __tablename__ = "revenue_ownership_records"

    record_id = Column(
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
    owner_name_vernacular = Column(Text, nullable=False)
    owner_name_english = Column(Text, nullable=False)
    father_spouse_name = Column(Text, nullable=True)
    share_fraction = Column(String(20), default="1/1", server_default=text("'1/1'"))
    land_type = Column(String(50), nullable=True)
    encumbrance_status = Column(Text, nullable=True)
    ocr_confidence = Column(Numeric(4, 3), nullable=True)
    raw_document_url = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # ── Relationships ────────────────────────────────────────────────
    parcel = relationship("CadastralParcel", back_populates="ownership_records")

    def __repr__(self) -> str:
        return (
            f"<RevenueOwnershipRecord(owner={self.owner_name_english!r}, "
            f"share={self.share_fraction!r})>"
        )
