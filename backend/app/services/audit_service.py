"""
BhuSynch AI — Audit Service
==============================
Merkle hash chain operations and verification for the
immutable provenance ledger (Section 2.5).
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from app.models.audit_ledger import CadastralAuditLedger
from app.provenance.merkle_tree import MerkleTree
from app.provenance.dsc_signer import DSCSigner

logger = structlog.get_logger(__name__)


class AuditService:
    """
    Service for managing the immutable Merkle audit ledger.
    Each operation creates a tamper-proof hash chain entry.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.merkle = MerkleTree()
        self.signer = DSCSigner()

    async def get_latest_hash(self, ulpin: str) -> str:
        """Get the latest Merkle hash for a ULPIN."""
        stmt = (
            select(CadastralAuditLedger)
            .where(CadastralAuditLedger.ulpin == ulpin)
            .order_by(CadastralAuditLedger.entry_id.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        entry = result.scalar_one_or_none()

        return entry.current_hash if entry else MerkleTree.GENESIS_HASH

    async def create_audit_entry(
        self,
        ulpin: str,
        event_type: str,
        officer_id: str,
        geom_wkb: bytes,
        payload: Dict[str, Any],
    ) -> CadastralAuditLedger:
        """
        Create a new audit ledger entry with Merkle hash and DSC signature.

        Parameters:
            ulpin: Parcel ULPIN
            event_type: RECTIFICATION, MUTATION, or ADJUDICATION
            officer_id: Authorized officer ID
            geom_wkb: WKB geometry bytes
            payload: Event data payload
        """
        prev_hash = await self.get_latest_hash(ulpin)

        # Create Merkle entry
        merkle_entry = MerkleTree.create_entry(
            ulpin=ulpin,
            officer_id=officer_id,
            geom_wkb=geom_wkb,
            prev_hash=prev_hash,
            payload=payload,
        )

        # Sign with DSC
        sign_data = f"{merkle_entry.current_hash}:{ulpin}:{officer_id}".encode()
        dsc_sig = self.signer.sign(sign_data, officer_id)

        # Persist to database
        ledger_entry = CadastralAuditLedger(
            ulpin=ulpin,
            event_type=event_type,
            officer_id=officer_id,
            prev_merkle_hash=prev_hash,
            current_hash=merkle_entry.current_hash,
            dsc_signature=dsc_sig.signature,
            payload_snapshot=payload,
        )

        self.db.add(ledger_entry)
        await self.db.flush()

        logger.info(
            "audit_entry_created",
            ulpin=ulpin,
            event=event_type,
            hash=merkle_entry.current_hash[:16] + "...",
        )

        return ledger_entry

    async def verify_chain(self, ulpin: str) -> Dict[str, Any]:
        """
        Verify the complete Merkle hash chain for a ULPIN.
        Returns verification result for judicial non-repudiation.
        """
        stmt = (
            select(CadastralAuditLedger)
            .where(CadastralAuditLedger.ulpin == ulpin)
            .order_by(CadastralAuditLedger.entry_id.asc())
        )
        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        if not entries:
            return {
                "ulpin": ulpin,
                "chain_length": 0,
                "is_valid": True,
                "message": "No audit entries found — empty chain is valid.",
            }

        # Verify hash chain integrity
        is_valid = True
        broken_at = None
        prev_hash = MerkleTree.GENESIS_HASH

        for i, entry in enumerate(entries):
            if entry.prev_merkle_hash != prev_hash:
                is_valid = False
                broken_at = i
                break
            prev_hash = entry.current_hash

        chain_data = [
            {
                "entry_id": e.entry_id,
                "event_type": e.event_type,
                "officer_id": e.officer_id,
                "hash": e.current_hash,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in entries
        ]

        return {
            "ulpin": ulpin,
            "chain_length": len(entries),
            "is_valid": is_valid,
            "broken_at": broken_at,
            "chain": chain_data,
        }
