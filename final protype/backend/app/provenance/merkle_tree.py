"""
BhuSynch AI — SHA3-256 Merkle Tree Immutable Provenance Ledger
================================================================
Subsystem 5: Cryptographic Provenance

Exact formula from Section 2.5:
H_k = SHA3-256(ULPIN ‖ Timestamp ‖ Officer_ID ‖ Geom_WKB ‖ H_{k-1})

Provides judicial non-repudiation for land record changes.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


@dataclass
class MerkleEntry:
    """A single entry in the Merkle hash chain."""
    ulpin: str
    timestamp: str
    officer_id: str
    geom_wkb: bytes
    prev_hash: str
    current_hash: str
    payload: Dict[str, Any]

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)


class MerkleTree:
    """
    SHA3-256 Merkle Tree for immutable audit provenance.

    Each ULPIN has its own hash chain. Every modification to a parcel
    (rectification, mutation, adjudication) creates a new entry:

    H_k = SHA3-256(ULPIN ‖ Timestamp ‖ Officer_ID ‖ Geom_WKB ‖ H_{k-1})

    The chain is anchored to a genesis hash and can be verified
    independently for judicial non-repudiation.
    """

    GENESIS_HASH = settings.MERKLE_GENESIS_HASH

    def __init__(self, entries: Optional[List[MerkleEntry]] = None):
        self.chain: List[MerkleEntry] = entries or []

    @property
    def entries(self) -> List[MerkleEntry]:
        return self.chain

    @property
    def prev_hash(self) -> str:
        return self.chain[-1].current_hash if self.chain else self.GENESIS_HASH

    def append_entry(
        self,
        ulpin: Any = None,
        officer_id: str = "OFF-001",
        event_type: str = "MUTATION",
        geom_wkb: bytes = b"\x01\x03\x00\x00\x00",
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
        **kwargs,
    ) -> MerkleEntry:
        """Append a new entry to this instance's chain."""
        if isinstance(ulpin, dict):
            d = ulpin
            u_val = str(d.get("ulpin", ""))
            off_val = str(d.get("officer_id", officer_id))
            g_val = d.get("geom_wkb", geom_wkb)
            if isinstance(g_val, str):
                g_val = g_val.encode("utf-8")
            ts_val = d.get("timestamp")
            payload = {"event_type": d.get("event_type", event_type), **(d.get("metadata") or {})}
        else:
            u_val = str(ulpin) if ulpin is not None else ""
            off_val = str(officer_id)
            g_val = geom_wkb.encode("utf-8") if isinstance(geom_wkb, str) else geom_wkb
            ts_val = timestamp
            payload = {"event_type": event_type, **(metadata or {})}

        prev = self.chain[-1].current_hash if self.chain else self.GENESIS_HASH
        entry = self.create_entry(
            ulpin=u_val,
            officer_id=off_val,
            geom_wkb=g_val,
            prev_hash=prev,
            payload=payload,
            timestamp=ts_val,
        )
        self.chain.append(entry)
        return entry

    def get_root_hash(self) -> str:
        """Get the latest leaf hash or genesis hash."""
        return self.chain[-1].current_hash if self.chain else self.GENESIS_HASH

    def verify(self) -> bool:
        """Verify this instance's chain."""
        return self.verify_chain(self.chain)

    @staticmethod
    def compute_hash(
        ulpin: str,
        timestamp: str,
        officer_id: str,
        geom_wkb: bytes,
        prev_hash: str,
    ) -> str:
        """
        Compute SHA3-256 hash for a Merkle chain entry.

        Formula (Section 2.5):
        H_k = SHA3-256(ULPIN ‖ Timestamp ‖ Officer_ID ‖ Geom_WKB ‖ H_{k-1})
        """
        hasher = hashlib.sha3_256()
        hasher.update(str(ulpin).encode("utf-8"))
        hasher.update(b"||")
        hasher.update(str(timestamp).encode("utf-8"))
        hasher.update(b"||")
        hasher.update(str(officer_id).encode("utf-8"))
        hasher.update(b"||")
        if isinstance(geom_wkb, str):
            hasher.update(geom_wkb.encode("utf-8"))
        else:
            hasher.update(geom_wkb)
        hasher.update(b"||")
        hasher.update(str(prev_hash).encode("utf-8"))

        return hasher.hexdigest()

    @classmethod
    def create_entry(
        cls,
        ulpin: str,
        officer_id: str,
        geom_wkb: bytes,
        prev_hash: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ) -> MerkleEntry:
        """Create a new Merkle chain entry."""
        if prev_hash is None:
            prev_hash = cls.GENESIS_HASH

        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        current_hash = cls.compute_hash(
            ulpin=ulpin,
            timestamp=timestamp,
            officer_id=officer_id,
            geom_wkb=geom_wkb,
            prev_hash=prev_hash,
        )

        entry = MerkleEntry(
            ulpin=ulpin,
            timestamp=timestamp,
            officer_id=officer_id,
            geom_wkb=geom_wkb,
            prev_hash=prev_hash,
            current_hash=current_hash,
            payload=payload or {},
        )

        logger.info(
            "merkle_entry_created",
            ulpin=ulpin,
            hash=current_hash[:16] + "...",
        )

        return entry

    def verify_chain(self, entries: Optional[List[MerkleEntry]] = None) -> bool:
        """
        Verify the integrity of a Merkle hash chain.
        Can be called as an instance method without arguments (verifies self.chain)
        or with a specific entries list.
        """
        target_entries = self.chain if entries is None else entries
        return self._verify_entries(target_entries)

    @classmethod
    def _verify_entries(cls, entries: List[MerkleEntry]) -> bool:
        if not entries:
            return True

        for i, entry in enumerate(entries):
            expected_prev = cls.GENESIS_HASH if i == 0 else entries[i - 1].current_hash

            if entry.prev_hash != expected_prev:
                logger.error(
                    "merkle_chain_broken",
                    entry_index=i,
                    expected_prev=expected_prev[:16],
                    actual_prev=entry.prev_hash[:16],
                )
                return False

            recomputed = cls.compute_hash(
                ulpin=entry.ulpin,
                timestamp=entry.timestamp,
                officer_id=entry.officer_id,
                geom_wkb=entry.geom_wkb,
                prev_hash=entry.prev_hash,
            )

            if recomputed != entry.current_hash:
                logger.error(
                    "merkle_hash_mismatch",
                    entry_index=i,
                    expected=recomputed[:16],
                    actual=entry.current_hash[:16],
                )
                return False

        logger.info("merkle_chain_verified", length=len(entries), valid=True)
        return True

    @staticmethod
    def compute_tree_root(hashes: List[str]) -> str:
        """
        Compute Merkle tree root from a list of leaf hashes.
        Used for batch verification of multiple parcels.
        """
        if not hashes:
            return MerkleTree.GENESIS_HASH

        current_level = list(hashes)

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left

                combined = hashlib.sha3_256()
                combined.update(left.encode("utf-8"))
                combined.update(right.encode("utf-8"))
                next_level.append(combined.hexdigest())

            current_level = next_level

        return current_level[0]


compute_entry_hash = MerkleTree.compute_hash

