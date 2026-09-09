"""
BhuSynch AI — Cadastral Audit Ledger Model
=============================================
Maps to: Table 5 — cadastral_audit_ledger (Section 3 DDL)
Immutable Merkle Tree Provenance from Subsystem 5.

Hash chain formula (Section 2.5):
H_k = SHA3-256(ULPIN ‖ Timestamp ‖ Officer_ID ‖ Geom_WKB ‖ H_{k-1})

Digitally signed with DSC under Section 3, IT Act 2000.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class CadastralAuditLedger(Base):
    """
    Immutable tamper-proof audit ledger entry.

    Each entry forms part of a SHA3-256 Merkle hash chain per ULPIN.
    The chain provides judicial non-repudiation for land record changes.

    Event types: RECTIFICATION, MUTATION, ADJUDICATION
    """

    __tablename__ = "cadastral_audit_ledger"

    entry_id = Column(BigInteger, primary_key=True, autoincrement=True)
    ulpin = Column(String(14), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    officer_id = Column(String(100), nullable=False)
    prev_merkle_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False)
    dsc_signature = Column(Text, nullable=False)
    payload_snapshot = Column(JSONB, nullable=False)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    def __repr__(self) -> str:
        return (
            f"<CadastralAuditLedger(entry_id={self.entry_id}, "
            f"ulpin={self.ulpin!r}, event={self.event_type!r})>"
        )
