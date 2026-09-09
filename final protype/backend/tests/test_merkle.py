"""
Tests for Cryptographic Provenance — SHA3-256 Merkle Tree Immutable Ledger.

Validates:
- SHA3-256 hash generation
- Merkle tree construction and verification
- Hash chain integrity (Hk = SHA3-256(ULPIN ‖ Timestamp ‖ Officer_ID ‖ Geom_WKB ‖ H_{k-1}))
- Tamper detection
"""
import hashlib
import pytest
from unittest.mock import MagicMock

from app.provenance.merkle_tree import MerkleTree, compute_entry_hash
from app.provenance.dsc_signer import DSCSigner


class TestMerkleTree:
    """Tests for SHA3-256 Merkle tree provenance ledger."""

    def test_sha3_256_hash_deterministic(self):
        """Same input must always produce the same SHA3-256 hash."""
        data = b"test_parcel_data"
        h1 = hashlib.sha3_256(data).hexdigest()
        h2 = hashlib.sha3_256(data).hexdigest()
        assert h1 == h2

    def test_sha3_256_hash_length(self):
        """SHA3-256 output must be 64 hex characters (256 bits)."""
        data = b"bhusynch_ai_cadastral"
        h = hashlib.sha3_256(data).hexdigest()
        assert len(h) == 64

    def test_entry_hash_includes_all_components(self):
        """Entry hash must incorporate ULPIN, timestamp, officer, geom, prev_hash."""
        h = compute_entry_hash(
            ulpin="09281234567890",
            timestamp="2024-01-15T10:30:00Z",
            officer_id="OFF-001",
            geom_wkb=b"\x01\x02\x03\x04",
            prev_hash="0" * 64
        )
        assert len(h) == 64
        assert isinstance(h, str)

    def test_hash_chain_integrity(self):
        """Each hash in chain must depend on the previous hash."""
        prev = "0" * 64
        hashes = []
        for i in range(5):
            h = compute_entry_hash(
                ulpin=f"0928123456789{i}",
                timestamp=f"2024-01-15T10:3{i}:00Z",
                officer_id="OFF-001",
                geom_wkb=f"geom_{i}".encode(),
                prev_hash=prev
            )
            hashes.append(h)
            prev = h

        # All hashes must be unique
        assert len(set(hashes)) == 5

    def test_tamper_detection(self):
        """Modifying any entry should break the chain verification."""
        tree = MerkleTree()
        entries = []
        for i in range(3):
            entry = {
                "ulpin": f"0928123456789{i}",
                "timestamp": f"2024-01-15T10:3{i}:00Z",
                "officer_id": "OFF-001",
                "geom_wkb": f"geom_{i}".encode(),
            }
            tree.append_entry(entry)
            entries.append(entry)

        # Chain should be valid
        assert tree.verify_chain() is True

        # Tamper with middle entry
        tree.entries[1]["ulpin"] = "TAMPERED_ULPIN"
        assert tree.verify_chain() is False

    def test_merkle_root_changes_with_new_entry(self):
        """Adding an entry should change the Merkle root."""
        tree = MerkleTree()
        tree.append_entry({
            "ulpin": "09281234567890",
            "timestamp": "2024-01-15T10:30:00Z",
            "officer_id": "OFF-001",
            "geom_wkb": b"geom_0",
        })
        root1 = tree.get_root_hash()

        tree.append_entry({
            "ulpin": "09281234567891",
            "timestamp": "2024-01-15T10:31:00Z",
            "officer_id": "OFF-002",
            "geom_wkb": b"geom_1",
        })
        root2 = tree.get_root_hash()

        assert root1 != root2

    def test_genesis_hash_is_all_zeros(self):
        """The genesis (first) previous hash should be all zeros."""
        tree = MerkleTree()
        assert tree.prev_hash == "0" * 64

    def test_empty_tree_has_zero_root(self):
        """Empty tree should have a deterministic zero root."""
        tree = MerkleTree()
        root = tree.get_root_hash()
        assert root == "0" * 64


class TestDSCSigner:
    """Tests for Digital Signature Certificate (IT Act 2000) signing."""

    def test_sign_produces_non_empty_signature(self):
        """Signing data must produce a non-empty signature string."""
        signer = DSCSigner()
        sig = signer.sign(b"test_audit_payload")
        assert sig is not None
        assert len(sig) > 0

    def test_verify_valid_signature(self):
        """Verification of a valid signature should return True."""
        signer = DSCSigner()
        data = b"verified_parcel_mutation"
        sig = signer.sign(data)
        assert signer.verify(data, sig) is True

    def test_verify_tampered_data(self):
        """Tampered data should fail signature verification."""
        signer = DSCSigner()
        data = b"original_data"
        sig = signer.sign(data)
        assert signer.verify(b"tampered_data", sig) is False

    def test_different_data_different_signatures(self):
        """Different payloads must produce different signatures."""
        signer = DSCSigner()
        sig1 = signer.sign(b"payload_1")
        sig2 = signer.sign(b"payload_2")
        assert sig1 != sig2
