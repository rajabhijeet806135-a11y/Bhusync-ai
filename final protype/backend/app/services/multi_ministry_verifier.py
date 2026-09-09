"""
BhuSynch AI — National Cadastral Multi-Ministry Verification Engine
====================================================================
Standard: SIH 26013 / NAKSHA / DILRMP / ISO 19152 (LADM) / IT Act 2000

Implements authoritative multi-ministry validation rules, geodetic precision
verification, statutory corridor conflict arbitration, 3D cadastre checks,
and 7 Statutory Quality Gates adjudication dossier compilation.
"""

import math
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np
from shapely.geometry import Polygon, LineString, Point, MultiPolygon, shape, mapping
from shapely.ops import unary_union
import structlog

from app.provenance.dsc_signer import DSCSigner

logger = structlog.get_logger(__name__)


# ==============================================================================
# 1. GEODETIC & POSITIONAL ACCURACY CALCULATOR (MoST / Survey of India / ISRO)
# ==============================================================================

class GeodeticAccuracyVerifier:
    """
    Validates geodetic precision against Survey of India CORS network and ASPRS Class 1.
    """

    @staticmethod
    def calculate_horizontal_rmse(icp_coords: np.ndarray, observed_coords: np.ndarray) -> Dict[str, float]:
        """
        Compute horizontal RMSE_x, RMSE_y, RMSE_h and Circular Error 90% (CE90).
        """
        residuals = observed_coords - icp_coords
        dx = residuals[:, 0]
        dy = residuals[:, 1]

        rmse_x = float(np.sqrt(np.mean(dx ** 2)))
        rmse_y = float(np.sqrt(np.mean(dy ** 2)))
        rmse_h = float(np.sqrt(rmse_x ** 2 + rmse_y ** 2))
        ce90 = float(1.5175 * rmse_h)

        passed = bool((rmse_x <= 0.050) and (rmse_y <= 0.050) and (rmse_h <= 0.0598) and (ce90 <= 0.0908))

        return {
            "rmse_x_m": round(rmse_x, 4),
            "rmse_y_m": round(rmse_y, 4),
            "horizontal_rmse_m": round(rmse_h, 4),
            "ce90_m": round(ce90, 4),
            "passed": passed,
            "standard": "ASPRS 2014 Class 1 (1:1000 scale)",
        }

    @staticmethod
    def calculate_vertical_rmse(ground_z: np.ndarray, dsm_z: np.ndarray) -> Dict[str, float]:
        """
        Compute vertical RMSE_z and Linear Error 90% (LE90).
        """
        dz = dsm_z - ground_z
        rmse_z = float(np.sqrt(np.mean(dz ** 2)))
        le90 = float(1.6449 * rmse_z)

        passed = bool((rmse_z <= 0.100) and (le90 <= 0.1645))

        return {
            "vertical_rmse_m": round(rmse_z, 4),
            "le90_m": round(le90, 4),
            "passed": passed,
            "standard": "SoI / ISRO High-Precision Elevation Benchmark",
        }


# ==============================================================================
# 2. STATUTORY CORRIDOR & CROSS-MINISTRY CONFLICT DETECTOR
# ==============================================================================

class MultiMinistryConflictVerifier:
    """
    Validates inter-agency spatial constraints across Municipal, Utility, Waterways, and Transport layers.
    """

    @staticmethod
    def verify_dp_road_encroachment(parcel_geom: Polygon, road_centerline: LineString, sanctioned_width_m: float) -> Dict[str, Any]:
        """
        MoHUA / ULB Benchmark B3.1: Zero private parcel encroachment into sanctioned DP Road Right-of-Way.
        """
        road_row_polygon = road_centerline.buffer(sanctioned_width_m / 2.0, cap_style=2)
        intersection = parcel_geom.intersection(road_row_polygon)
        encroachment_area = float(intersection.area)

        return {
            "authority": "MoHUA / Urban Local Body (Town Planning)",
            "rule": f"DP {sanctioned_width_m}m Road Right-of-Way Invariant",
            "encroachment_area_sqm": round(encroachment_area, 4),
            "status": "CLEAR" if encroachment_area <= 1e-4 else "VIOLATION",
            "statutory_action": "None" if encroachment_area <= 1e-4 else "Issue Case B Anti-Encroachment Notice",
        }

    @staticmethod
    def verify_gas_pipeline_safety_buffer(parcel_or_building: Polygon, pipeline: LineString, pipeline_type: str = "STEEL_MAINS") -> Dict[str, Any]:
        """
        MoPNG / PNGRB Benchmark B4.1: Mandatory safety buffer corridor.
        Steel Mains: 5.0m buffer; MDPE Distribution: 2.0m buffer.
        """
        buffer_dist = 5.0 if pipeline_type.upper() == "STEEL_MAINS" else 2.0
        safety_corridor = pipeline.buffer(buffer_dist)
        clash = parcel_or_building.intersection(safety_corridor)
        clash_area = float(clash.area)

        return {
            "authority": "MoPNG / PNGRB",
            "rule": f"Petroleum Pipelines Act 1956 - {buffer_dist}m Safety Corridor Invariant",
            "buffer_distance_m": buffer_dist,
            "clash_area_sqm": round(clash_area, 4),
            "status": "CLEAR" if clash_area <= 1e-4 else "CRITICAL_SAFETY_VIOLATION",
            "statutory_action": "None" if clash_area <= 1e-4 else "Emergency Alert to District Disaster Authority & City Gas Parastatal",
        }

    @staticmethod
    def verify_waterbody_buffer(parcel_geom: Polygon, nala_or_river: LineString, width_m: float = 12.0) -> Dict[str, Any]:
        """
        Ministry of Jal Shakti / NGT Benchmark B5.1: Waterbody protection green buffer.
        Width < 10m -> 4.5m buffer; Width >= 10m -> 9.0m buffer; Major River -> 25-50m Blue Line.
        """
        buffer_dist = 9.0 if width_m >= 10.0 else 4.5
        green_belt = nala_or_river.buffer(buffer_dist)
        intrusion = parcel_geom.intersection(green_belt)
        intrusion_area = float(intrusion.area)

        return {
            "authority": "Ministry of Jal Shakti / National Green Tribunal",
            "rule": f"Statutory Waterbody {buffer_dist}m Green Belt Buffer",
            "buffer_distance_m": buffer_dist,
            "intrusion_area_sqm": round(intrusion_area, 4),
            "status": "CLEAR" if intrusion_area <= 1e-4 else "STATUTORY_WATERWAY_VIOLATION",
            "statutory_action": "None" if intrusion_area <= 1e-4 else "Mandatory River Protection Review under NGT Directives",
        }

    @staticmethod
    def verify_railway_setback(parcel_geom: Polygon, rail_track: LineString) -> Dict[str, Any]:
        """
        Ministry of Railways Benchmark B6.1: Indian Railways Act 1989.
        15.0m absolute exclusion zone, 30.0m deep foundation safety setback.
        """
        exclusion_15m = rail_track.buffer(15.0)
        setback_30m = rail_track.buffer(30.0)

        in_exclusion = float(parcel_geom.intersection(exclusion_15m).area)
        in_setback = float(parcel_geom.intersection(setback_30m).area)

        status = "CLEAR"
        action = "None"
        if in_exclusion > 1e-4:
            status = "CRITICAL_RAILWAY_EXCLUSION_VIOLATION"
            action = "Immediate Demolition Notice under Indian Railways Act 1989"
        elif in_setback > 1e-4:
            status = "RAILWAY_SAFETY_SETBACK_RESTRICTION"
            action = "Special Railway Engineering Board Clearance Required"

        return {
            "authority": "Ministry of Railways",
            "rule": "15m Structural Exclusion & 30m Deep Foundation Safety Zone",
            "exclusion_area_sqm": round(in_exclusion, 4),
            "setback_area_sqm": round(in_setback, 4),
            "status": status,
            "statutory_action": action,
        }


# ==============================================================================
# 3. 3D CONDOMINIUM CADASTRE VERIFIER (MoHUA / RERA / ISO 19152 LADM)
# ==============================================================================

class Cadastre3DVerifier:
    """
    Validates 3D strata volumetric closure and vertical strata interpenetration.
    """

    @staticmethod
    def verify_strata_enclosure(floors: List[Dict[str, float]], total_building_envelope_volume: float) -> Dict[str, Any]:
        """
        Benchmark B3.3 & B3.4: Volumetric enclosure and zero Z-interpenetration.
        """
        # Sort floors by z_min
        sorted_floors = sorted(floors, key=lambda f: f["z_min"])

        # 1. Zero Z-axis interpenetration
        interpenetrations = []
        for i in range(len(sorted_floors) - 1):
            curr_floor = sorted_floors[i]
            next_floor = sorted_floors[i + 1]

            if curr_floor["z_max"] > next_floor["z_min"] + 1e-3:
                interpenetrations.append({
                    "floor_pair": (i + 1, i + 2),
                    "overlap_z_m": round(curr_floor["z_max"] - next_floor["z_min"], 4)
                })

        # 2. Total volume closure
        sum_unit_volumes = sum(f.get("volume", f.get("area", 0.0) * (f.get("z_max", 0.0) - f.get("z_min", 0.0))) for f in floors)
        vol_error_pct = abs(sum_unit_volumes - total_building_envelope_volume) / total_building_envelope_volume * 100.0

        closure_passed = bool(vol_error_pct <= 0.50)
        strata_clean = bool(len(interpenetrations) == 0)

        return {
            "standard": "ISO 19152 LADM 3D Strata Enclosure",
            "total_unit_volume_m3": round(sum_unit_volumes, 3),
            "building_envelope_volume_m3": round(total_building_envelope_volume, 3),
            "volumetric_closure_error_pct": round(vol_error_pct, 4),
            "volumetric_closure_passed": closure_passed,
            "interpenetration_count": len(interpenetrations),
            "interpenetrations": interpenetrations,
            "strata_valid": closure_passed and strata_clean,
        }


# ==============================================================================
# 4. AREA DISCREPANCY & ULPIN VALIDATOR (MoRD / DoLR / NAKSHA)
# ==============================================================================

class CadastralLegalAreaVerifier:
    """
    Validates legal Jamabandi recorded area against observed drone polygon area.
    """

    @staticmethod
    def verify_area_tolerance(legal_area_sqm: float, observed_area_sqm: float, is_urban: bool = True) -> Dict[str, Any]:
        """
        Benchmark B1.2: Area tolerance <= 2.0% (Urban), <= 5.0% (Rural).
        """
        threshold = 2.0 if is_urban else 5.0
        delta_pct = abs(observed_area_sqm - legal_area_sqm) / legal_area_sqm * 100.0
        passed = bool(delta_pct <= threshold)

        return {
            "legal_area_sqm": legal_area_sqm,
            "observed_area_sqm": observed_area_sqm,
            "discrepancy_sqm": round(abs(observed_area_sqm - legal_area_sqm), 4),
            "delta_percentage": round(delta_pct, 4),
            "threshold_percentage": threshold,
            "zone_type": "URBAN" if is_urban else "RURAL",
            "passed": passed,
            "statutory_route": "Automated Certification" if passed else "Route to Case A Revenue Officer Arbitration",
        }

    @staticmethod
    def validate_ulpin(ulpin: str, state_code: str = "27") -> bool:
        """
        Validate 14-character ULPIN standard format and state prefix.
        """
        if len(ulpin) != 14:
            return False
        if not ulpin.isalnum():
            return False
        if not ulpin.startswith(state_code):
            return False
        return True


# ==============================================================================
# 5. MERKLE PROVENANCE & CRYPTOGRAPHIC LEDGER (MeitY / IT Act 2000)
# ==============================================================================

class MerkleProvenanceEngine:
    """
    Computes SHA3-256 Merkle chain hashes for immutable auditability.
    """

    @staticmethod
    def compute_mutation_hash(ulpin: str, timestamp_iso: str, officer_id: str, geom_wkb_hex: str, prev_hash: str) -> str:
        """
        H_k = SHA3-256(ULPIN || Timestamp || Officer_ID || Geom_WKB || H_{k-1})
        """
        payload = f"{ulpin}:{timestamp_iso}:{officer_id}:{geom_wkb_hex}:{prev_hash}".encode("utf-8")
        return hashlib.sha3_256(payload).hexdigest()

    @staticmethod
    def verify_merkle_chain(chain: List[Dict[str, str]]) -> bool:
        """
        Verify cryptographic integrity across sequential chain blocks.
        """
        if not chain:
            return True

        for i in range(1, len(chain)):
            prev_block = chain[i - 1]
            curr_block = chain[i]

            expected_hash = MerkleProvenanceEngine.compute_mutation_hash(
                ulpin=curr_block["ulpin"],
                timestamp_iso=curr_block["timestamp"],
                officer_id=curr_block["officer_id"],
                geom_wkb_hex=curr_block["geom_wkb"],
                prev_hash=prev_block["hash"]
            )
            if curr_block["hash"] != expected_hash:
                return False

        return True


# ==============================================================================
# 6. SEVEN STATUTORY ADJUDICATION QUALITY GATES ORCHESTRATOR
# ==============================================================================

class StatutoryQualityGateOrchestrator:
    """
    Executes the 7 Statutory Adjudication Quality Gates and compiles the
    official Adjudication Dossier conforming to the DoLR NAKSHA JSON Schema.
    """

    def __init__(self):
        self.signer = DSCSigner()

    def evaluate_gates_and_compile_dossier(
        self,
        parcel_context: Dict[str, Any],
        survey_icps: Dict[str, np.ndarray],
        parcel_poly: Polygon,
        adjoining_parcels: List[Polygon],
        statutory_layers: Dict[str, Any],
        ocr_metrics: Dict[str, float],
        covariance_semi_major_m: float,
        officer_id: str = "City Survey Officer No. 1, Pune",
        dsc_cert_serial: str = "MH-REV-PUN-0091823-2026",
    ) -> Dict[str, Any]:
        """
        Run all 7 Quality Gates and generate the signed Statutory Adjudication Dossier.
        """
        gate_results = {}

        # GATE 1: Geodetic Anchor Lock
        geodetic_res = GeodeticAccuracyVerifier.calculate_horizontal_rmse(
            survey_icps["icp"], survey_icps["drone"]
        )
        gate_results["GATE_1_GEODETIC_ANCHOR"] = {
            "passed": geodetic_res["passed"],
            "horizontal_rmse_m": geodetic_res["horizontal_rmse_m"],
            "ce90_m": geodetic_res["ce90_m"],
        }

        # GATE 2: Topo-Geometric Sanity
        is_valid = parcel_poly.is_valid
        has_min_area = parcel_poly.area >= 0.05
        overlaps = []
        for i, adj in enumerate(adjoining_parcels):
            inter_area = parcel_poly.intersection(adj).area
            if inter_area > 1e-4:
                overlaps.append({"adjoining_index": i, "overlap_area": inter_area})

        gate_results["GATE_2_TOPO_GEOMETRIC_SANITY"] = {
            "passed": is_valid and has_min_area and (len(overlaps) == 0),
            "st_is_valid": is_valid,
            "no_slivers": has_min_area,
            "zero_overlaps": len(overlaps) == 0,
        }

        # GATE 3: Statutory Corridor Shield
        dp_res = MultiMinistryConflictVerifier.verify_dp_road_encroachment(
            parcel_poly, statutory_layers["dp_road_centerline"], statutory_layers.get("dp_road_width", 24.0)
        )
        gas_res = MultiMinistryConflictVerifier.verify_gas_pipeline_safety_buffer(
            parcel_poly, statutory_layers["gas_pipeline"]
        )
        water_res = MultiMinistryConflictVerifier.verify_waterbody_buffer(
            parcel_poly, statutory_layers["waterbody_line"]
        )
        rail_res = MultiMinistryConflictVerifier.verify_railway_setback(
            parcel_poly, statutory_layers["railway_track"]
        )

        all_corridors_clear = (
            dp_res["status"] == "CLEAR"
            and gas_res["status"] == "CLEAR"
            and water_res["status"] == "CLEAR"
            and rail_res["status"] == "CLEAR"
        )

        gate_results["GATE_3_STATUTORY_CORRIDOR_SHIELD"] = {
            "passed": all_corridors_clear,
            "dp_road": dp_res["status"],
            "gas_pipeline": gas_res["status"],
            "waterbody": water_res["status"],
            "railway": rail_res["status"],
        }

        # GATE 4: Indic Document AI Match
        area_check = CadastralLegalAreaVerifier.verify_area_tolerance(
            parcel_context["legal_area_sqm"], parcel_poly.area, is_urban=True
        )
        cer = ocr_metrics.get("cer", 0.015)
        wer = ocr_metrics.get("wer", 0.032)
        doc_ai_passed = area_check["passed"] and (cer <= 0.02) and (wer <= 0.045)

        gate_results["GATE_4_INDIC_DOCUMENT_AI_MATCH"] = {
            "passed": doc_ai_passed,
            "area_delta_pct": area_check["delta_percentage"],
            "cer": cer,
            "wer": wer,
        }

        # GATE 5: Error Covariance Bound
        cov_passed = covariance_semi_major_m <= 0.150
        gate_results["GATE_5_ERROR_COVARIANCE_BOUND"] = {
            "passed": cov_passed,
            "semi_major_axis_a_m": covariance_semi_major_m,
            "confidence_level": "95%",
        }

        # GATE 6: SHA3-256 Merkle Commit
        timestamp_iso = datetime.now(timezone.utc).isoformat()
        wkb_hex = parcel_poly.wkb_hex
        prev_hash = parcel_context.get("prev_hash", "0" * 64)
        merkle_root = MerkleProvenanceEngine.compute_mutation_hash(
            parcel_context["ulpin"], timestamp_iso, officer_id, wkb_hex, prev_hash
        )
        gate_results["GATE_6_MERKLE_COMMIT"] = {
            "passed": True,
            "merkle_root_hash": merkle_root,
        }

        # GATE 7: Digital Signature Certificate (DSC)
        sig_data = f"{merkle_root}:{officer_id}:{dsc_cert_serial}".encode("utf-8")
        dsc_signature = self.signer.sign(sig_data, officer_id)
        gate_results["GATE_7_DSC_SIGNATURE"] = {
            "passed": True,
            "signature": dsc_signature.signature,
            "algorithm": dsc_signature.algorithm,
            "signing_authority": officer_id,
        }

        all_gates_cleared = all(g["passed"] for g in gate_results.values())

        # Compile Official Statutory Dossier (Section 6 Schema)
        dossier = {
            "$schema": "https://naksha.dolr.gov.in/schemas/adjudication_dossier_v1.json",
            "dossier_id": f"DOS-PUN-HAV-{datetime.now().year}-{uuid4().hex[:6].upper()}",
            "ulpin": parcel_context["ulpin"],
            "khasra_no": parcel_context["khasra_no"],
            "state": parcel_context.get("state", "Maharashtra"),
            "district": parcel_context.get("district", "Pune"),
            "taluka": parcel_context.get("taluka", "Haveli"),
            "village": parcel_context.get("village", "Sadashiv Peth"),
            "all_quality_gates_cleared": all_gates_cleared,
            "quality_gates": gate_results,
            "geodetic_metrics": {
                "crs": "EPSG:7755 (WGS 84 / India NSF LCC)",
                "base_station": "Survey of India CORS PUN1",
                "horizontal_rmse_m": geodetic_res["horizontal_rmse_m"],
                "ce90_m": geodetic_res["ce90_m"],
                "observed_area_sqm": round(parcel_poly.area, 4),
                "legal_area_sqm": float(parcel_context["legal_area_sqm"]),
                "area_delta_pct": area_check["delta_percentage"],
            },
            "inter_agency_clearances": {
                "pmc_dp_road_row": f"{'CLEAR' if dp_res['status'] == 'CLEAR' else 'VIOLATION'} ({dp_res['encroachment_area_sqm']} m2 overlap with DP road)",
                "mngl_city_gas_pipeline": f"{'CLEAR' if gas_res['status'] == 'CLEAR' else 'VIOLATION'} ({gas_res['clash_area_sqm']} m2 clash with 5.0m buffer)",
                "jal_shakti_nala_buffer": f"{'CLEAR' if water_res['status'] == 'CLEAR' else 'VIOLATION'} ({water_res['intrusion_area_sqm']} m2 intrusion in buffer)",
                "railway_setback_zone": f"{'CLEAR' if rail_res['status'] == 'CLEAR' else 'VIOLATION'} ({rail_res['exclusion_area_sqm']} m2 exclusion clash)",
            },
            "cryptographic_provenance": {
                "merkle_root_hash": merkle_root,
                "signing_authority": officer_id,
                "dsc_cert_serial": dsc_cert_serial,
                "statutory_act": "Section 3, Indian Information Technology Act 2000",
                "timestamp": timestamp_iso,
            },
        }

        return dossier
