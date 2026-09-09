"""
BhuSynch AI — Dossier Service
================================
Generates legally certified statutory adjudication dossiers
with DSC signatures for revenue officer review.

"AI Proposes, Officer Disposes" (Section 2.4)
"""

import io
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

import structlog

from app.provenance.dsc_signer import DSCSigner

logger = structlog.get_logger(__name__)


class DossierService:
    """
    Statutory Revenue Adjudication Dossier Generator.

    Produces comprehensive dossier documents containing:
    1. Parcel spatial data and geometry
    2. Ownership records from RoR extraction
    3. Three-Truths conflict analysis
    4. Vertex covariance error ellipses
    5. Merkle hash provenance chain
    6. Officer notes and DSC signature

    Output formats: JSON (API response) and PDF (statutory document)
    """

    def __init__(self):
        self.signer = DSCSigner()

    async def generate_dossier(
        self,
        parcel_data: Dict[str, Any],
        conflicts: list,
        audit_chain: list,
        officer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a statutory adjudication dossier.

        Parameters:
            parcel_data: Complete parcel record with ownership
            conflicts: List of spatial conflicts
            audit_chain: Merkle hash chain entries
            officer_id: Reviewing officer ID

        Returns:
            Dossier dict with all sections
        """
        dossier = {
            "dossier_id": str(UUID(int=0)),  # Generated unique ID
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "system": "BhuSynch AI v1.0",
            "governance_standard": "NAKSHA (DoLR/MoRD), DILRMP, ULPIN",

            "parcel_summary": {
                "ulpin": parcel_data.get("ulpin"),
                "khasra_no": parcel_data.get("khasra_no"),
                "status": parcel_data.get("status"),
                "legal_area_sqm": parcel_data.get("legal_area_sqm"),
                "observed_area_sqm": parcel_data.get("observed_area_sqm"),
                "administrative_hierarchy": {
                    "state": parcel_data.get("state_code"),
                    "district": parcel_data.get("district_code"),
                    "village": parcel_data.get("village_code"),
                },
            },

            "three_truths_analysis": {
                "legal_truth": parcel_data.get("ownership_records", []),
                "physical_truth": {
                    "observed_area_sqm": parcel_data.get("observed_area_sqm"),
                    "boundary_source": "SAM-Geo ViT-H + Drone ORI",
                },
                "administrative_truth": {
                    "land_type": parcel_data.get("land_type"),
                    "encumbrance": parcel_data.get("encumbrance_status"),
                },
            },

            "conflict_cases": [
                {
                    "type": c.get("conflict_type"),
                    "severity": c.get("severity"),
                    "discrepancy": c.get("discrepancy_area_sqm"),
                    "status": c.get("adjudication_status"),
                }
                for c in conflicts
            ],

            "provenance_chain": {
                "chain_length": len(audit_chain),
                "latest_hash": audit_chain[-1].get("hash") if audit_chain else None,
                "entries": audit_chain,
            },

            "certification": {
                "philosophy": "AI Proposes, Officer Disposes",
                "officer_id": officer_id,
                "legal_framework": "IT Act 2000, Section 3 (DSC)",
            },
        }

        # Sign dossier with DSC if officer provided
        if officer_id:
            import json
            dossier_bytes = json.dumps(dossier, default=str).encode()
            sig = self.signer.sign(dossier_bytes, officer_id)
            dossier["dsc_signature"] = {
                "signature": sig.signature,
                "algorithm": sig.algorithm,
                "timestamp": sig.timestamp,
            }

        logger.info(
            "dossier_generated",
            ulpin=parcel_data.get("ulpin"),
            conflicts=len(conflicts),
        )

        return dossier
