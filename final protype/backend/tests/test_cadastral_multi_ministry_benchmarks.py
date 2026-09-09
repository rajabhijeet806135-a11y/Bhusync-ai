"""
National Cadastral Multi-Ministry Validation & Testing Benchmark Suite
=======================================================================
Standard: SIH 26013 / NAKSHA / DILRMP / ISO 19152 (LADM) / IT Act 2000

Verifies authoritative compliance across:
1. MoRD / DoLR (Cadastral Maps & Jamabandi, ULPIN, Metric Area Δ <= 2.0%)
2. MoST / SoI & ISRO (5cm Drone ORI, Horizontal RMSE <= 0.05m, CE90 <= 0.0908m, CORS PUN1)
3. MoHUA / ULB (Sanctioned DP Road RoW Zero Encroachment, 3D Strata Enclosure)
4. MoPNG / PNGRB (125mm MDPE 2.0m & 16-bar Steel 5.0m Subterranean Buffer)
5. Ministry of Jal Shakti (Nala 4.5m/9.0m Green Belt & River Blue Line)
6. Ministry of Railways & NHAI (15m/30m Safety Setbacks & Highway RoW)
7. MeitY / NIC (SHA3-256 Merkle Ledger & X.509 DSC Non-Repudiation)
8. End-to-End 7 Statutory Adjudication Quality Gates & Dossier Schema
"""

import math
import pytest
import numpy as np
from shapely.geometry import Polygon, LineString, Point, MultiPolygon
from shapely.ops import unary_union

from app.services.multi_ministry_verifier import (
    GeodeticAccuracyVerifier,
    MultiMinistryConflictVerifier,
    Cadastre3DVerifier,
    CadastralLegalAreaVerifier,
    MerkleProvenanceEngine,
    StatutoryQualityGateOrchestrator,
)


# ==============================================================================
# 1. GEODETIC & POSITIONAL ACCURACY BENCHMARK FIXTURES & TESTS (MoST / SoI)
# ==============================================================================

@pytest.fixture
def surveyed_icps_and_drone_points():
    """
    Independent Check Points (ICPs) surveyed via Survey of India CORS PUN1 (RTK DGNSS)
    compared against 5cm Drone Orthomosaic extracted coordinates (EPSG:7755).
    """
    np.random.seed(42)
    # Ground Truth ICP Coordinates (Easting, Northing in EPSG:7755 meters)
    icp_coords = np.array([
        [385420.125, 2048910.450],
        [385550.890, 2048935.120],
        [385610.340, 2049050.880],
        [385730.560, 2049120.330],
        [385810.770, 2049240.670],
        [385900.210, 2049310.440],
        [385480.650, 2049380.220],
        [385390.430, 2049220.910],
        [385670.110, 2049180.750],
        [385750.950, 2049010.550]
    ])
    
    # Drone extracted coordinates with realistic sub-5cm gaussian noise
    drone_coords = icp_coords + np.random.normal(loc=0.0, scale=0.025, size=icp_coords.shape)
    
    return {"icp": icp_coords, "drone": drone_coords}


def test_asprs_class1_horizontal_rmse_benchmark(surveyed_icps_and_drone_points):
    """
    Benchmark B2.1: Horizontal RMSE must be <= 0.0598m and CE90 <= 0.0908m (1:1000 scale).
    Reference: Kurniawan (2026), Suwardhi et al. (2025).
    """
    icp = surveyed_icps_and_drone_points["icp"]
    drone = surveyed_icps_and_drone_points["drone"]
    
    res = GeodeticAccuracyVerifier.calculate_horizontal_rmse(icp, drone)
    
    assert res["rmse_x_m"] <= 0.050, f"RMSE_x {res['rmse_x_m']}m exceeds 5cm tolerance"
    assert res["rmse_y_m"] <= 0.050, f"RMSE_y {res['rmse_y_m']}m exceeds 5cm tolerance"
    assert res["horizontal_rmse_m"] <= 0.0598, f"Horizontal RMSE {res['horizontal_rmse_m']}m exceeds 0.0598m benchmark"
    assert res["ce90_m"] <= 0.0908, f"CE90 {res['ce90_m']}m exceeds 0.0908m benchmark"
    assert res["passed"] is True


def test_vertical_elevation_accuracy_benchmark():
    """
    Benchmark B2.2: Vertical RMSE_z <= 0.100m, LE90 <= 0.1645m.
    """
    np.random.seed(42)
    ground_z = np.array([560.12, 560.45, 561.02, 559.88, 562.30, 561.95, 560.70, 560.10])
    dsm_z = ground_z + np.random.normal(loc=0.0, scale=0.045, size=ground_z.shape)

    res = GeodeticAccuracyVerifier.calculate_vertical_rmse(ground_z, dsm_z)
    assert res["vertical_rmse_m"] <= 0.100
    assert res["le90_m"] <= 0.1645
    assert res["passed"] is True


# ==============================================================================
# 2. TOPOLOGICAL INTEGRITY & CONSTRAINED TRIANGULATION BENCHMARK (MoRD / DoLR)
# ==============================================================================

@pytest.fixture
def multi_ward_cadastral_cluster():
    """
    A collection of adjoining urban cadastral parcels (Kasba Peth / Shivajinagar Ward).
    """
    p1 = Polygon([(0, 0), (50, 0), (50, 40), (0, 40), (0, 0)])
    p2 = Polygon([(50, 0), (100, 0), (100, 40), (50, 40), (50, 0)])
    p3 = Polygon([(0, 40), (50, 40), (50, 80), (0, 80), (0, 40)])
    p4 = Polygon([(50, 40), (100, 40), (100, 80), (50, 80), (50, 40)])
    
    return [p1, p2, p3, p4]


def test_topological_invariants_and_zero_overlaps(multi_ward_cadastral_cluster):
    """
    Benchmark B1.3: Topological Invariants (ST_IsValid = TRUE, ST_Overlaps = 0, Slivers = 0).
    """
    parcels = multi_ward_cadastral_cluster
    
    for i, p in enumerate(parcels):
        assert p.is_valid, f"Parcel {i} is topologically invalid: {p.explain_validity()}"
        assert p.area > 0.05, f"Parcel {i} is an illegal micro-sliver ({p.area} m2)"
    
    # Pairwise overlap verification
    for i in range(len(parcels)):
        for j in range(i + 1, len(parcels)):
            intersection = parcels[i].intersection(parcels[j])
            assert intersection.area == 0.0, (
                f"Topological Overlap detected between Parcel {i} and {j}: "
                f"Intersection Area = {intersection.area:.4f} m2"
            )


# ==============================================================================
# 3. STATUTORY MULTI-MINISTRY SPATIAL CONFLICT TESTS
# ==============================================================================

def test_pmc_dp_road_right_of_way_encroachment_benchmark():
    """
    Benchmark B3.1: Ministry of Housing & Urban Affairs / PMC Town Planning.
    Verification of zero private parcel encroachment into sanctioned DP Road Corridors.
    """
    # Sanctioned 24m DP Road Corridor Centerline
    road_centerline = LineString([(0, 100), (200, 100)])
    sanctioned_width = 24.0  # 12m on either side
    
    # Compliant Legal Parcel (Setback respected: starts at y=115, road buffer extends to y=112)
    compliant_parcel = Polygon([(10, 115), (60, 115), (60, 160), (10, 160), (10, 115)])
    res_compliant = MultiMinistryConflictVerifier.verify_dp_road_encroachment(compliant_parcel, road_centerline, sanctioned_width)
    assert res_compliant["status"] == "CLEAR"
    assert res_compliant["encroachment_area_sqm"] == 0.0
    
    # Encroaching Parcel (Extends 3m into DP Road: y=109 to 112 is within buffer)
    encroaching_parcel = Polygon([(70, 109), (120, 109), (120, 150), (70, 150), (70, 109)])
    res_encroach = MultiMinistryConflictVerifier.verify_dp_road_encroachment(encroaching_parcel, road_centerline, sanctioned_width)
    assert res_encroach["status"] == "VIOLATION"
    assert math.isclose(res_encroach["encroachment_area_sqm"], 50.0 * 3.0, rel_tol=1e-2)


def test_mopng_city_gas_pipeline_safety_buffer_benchmark():
    """
    Benchmark B4.1: Ministry of Petroleum & Natural Gas / PNGRB safety regulations.
    Zero permanent structures allowed within 5.0m buffer corridor of 16-bar gas mains.
    """
    gas_pipeline = LineString([(500, 0), (500, 300)])
    
    # Safe structure located 10m away
    safe_structure = Polygon([(510, 50), (530, 50), (530, 70), (510, 70), (510, 50)])
    res_safe = MultiMinistryConflictVerifier.verify_gas_pipeline_safety_buffer(safe_structure, gas_pipeline, "STEEL_MAINS")
    assert res_safe["status"] == "CLEAR"
    assert res_safe["clash_area_sqm"] == 0.0
    
    # Unauthorized boundary wall constructed over pipeline (x: 498 to 504 intersects x: 495 to 505)
    unauthorized_structure = Polygon([(498, 50), (504, 50), (504, 70), (498, 70), (498, 50)])
    res_clash = MultiMinistryConflictVerifier.verify_gas_pipeline_safety_buffer(unauthorized_structure, gas_pipeline, "STEEL_MAINS")
    assert res_clash["status"] == "CRITICAL_SAFETY_VIOLATION"
    assert res_clash["clash_area_sqm"] > 0.0


def test_jal_shakti_river_nala_blue_line_buffer_benchmark():
    """
    Benchmark B5.1: Ministry of Jal Shakti / NGT River Protection.
    Statutory 9.0m green buffer along natural Nalas (Gair Mumkin Nala).
    """
    nala_centerline = LineString([(0, 0), (100, 50), (200, 40)])
    
    # Safe parcel far away
    safe_parcel = Polygon([(10, 80), (50, 80), (50, 120), (10, 120), (10, 80)])
    res_safe = MultiMinistryConflictVerifier.verify_waterbody_buffer(safe_parcel, nala_centerline, width_m=12.0)
    assert res_safe["status"] == "CLEAR"
    
    # Violating parcel intruding into 9.0m buffer
    private_khasra = Polygon([(40, 25), (80, 25), (80, 60), (40, 60), (40, 25)])
    res_violation = MultiMinistryConflictVerifier.verify_waterbody_buffer(private_khasra, nala_centerline, width_m=12.0)
    assert res_violation["status"] == "STATUTORY_WATERWAY_VIOLATION"
    assert res_violation["intrusion_area_sqm"] > 0.0


def test_railway_setback_safety_zone_benchmark():
    """
    Benchmark B6.1: Ministry of Railways / Indian Railways Act 1989.
    15m absolute structural exclusion and 30m deep foundation setback zone.
    """
    rail_track = LineString([(0, 0), (500, 0)])
    
    # Safe parcel 40m away
    safe_parcel = Polygon([(50, 40), (100, 40), (100, 80), (50, 80), (50, 40)])
    res_safe = MultiMinistryConflictVerifier.verify_railway_setback(safe_parcel, rail_track)
    assert res_safe["status"] == "CLEAR"
    
    # Setback zone intrusion (20m away: within 30m setback, outside 15m exclusion)
    setback_parcel = Polygon([(50, 20), (100, 20), (100, 50), (50, 50), (50, 20)])
    res_setback = MultiMinistryConflictVerifier.verify_railway_setback(setback_parcel, rail_track)
    assert res_setback["status"] == "RAILWAY_SAFETY_SETBACK_RESTRICTION"
    
    # Absolute exclusion zone violation (within 15m)
    exclusion_parcel = Polygon([(50, 5), (100, 5), (100, 25), (50, 25), (50, 5)])
    res_excl = MultiMinistryConflictVerifier.verify_railway_setback(exclusion_parcel, rail_track)
    assert res_excl["status"] == "CRITICAL_RAILWAY_EXCLUSION_VIOLATION"


# ==============================================================================
# 4. INDIC DOCUMENT AI & ULPIN BOUNDING BENCHMARK (MoRD / DoLR)
# ==============================================================================

def test_ulpin_checksum_and_area_tolerance_benchmark():
    """
    Benchmark B1.2 & B1.4: 14-Character ULPIN Centroid Encoding & Area Delta.
    """
    recorded_legal_area_sqm = 1250.00
    
    # Observed Polygon from 5cm Drone ORI Conflation (1249.7225 m2)
    observed_polygon = Polygon([(100, 100), (135.35, 100), (135.35, 135.35), (100, 135.35), (100, 100)])
    
    res = CadastralLegalAreaVerifier.verify_area_tolerance(recorded_legal_area_sqm, observed_polygon.area, is_urban=True)
    assert res["passed"] is True
    assert res["delta_percentage"] <= 2.00
    
    # 14-Character ULPIN Verification
    ulpin_candidate = "27010410010002"
    assert CadastralLegalAreaVerifier.validate_ulpin(ulpin_candidate, state_code="27") is True
    assert CadastralLegalAreaVerifier.validate_ulpin("INVALID_ULPIN", state_code="27") is False


# ==============================================================================
# 5. 3D CONDOMINIUM CADASTRE BENCHMARK (MoHUA / RERA / ISO 19152 LADM)
# ==============================================================================

def test_3d_high_rise_strata_volumetric_enclosure_benchmark():
    """
    Benchmark B3.3 & B3.4: Volumetric polyhedral enclosure and zero Z-interpenetration.
    """
    footprint_area = 200.0  # m2
    floor_height = 3.0      # meters
    
    floor_1 = {"z_min": 0.0, "z_max": 3.0, "area": footprint_area, "volume": footprint_area * floor_height}
    floor_2 = {"z_min": 3.0, "z_max": 6.0, "area": footprint_area, "volume": footprint_area * floor_height}
    floor_3 = {"z_min": 6.0, "z_max": 9.0, "area": footprint_area, "volume": footprint_area * floor_height}
    
    floors = [floor_1, floor_2, floor_3]
    total_building_envelope_volume = footprint_area * 9.0  # 1800 m3
    
    res = Cadastre3DVerifier.verify_strata_enclosure(floors, total_building_envelope_volume)
    assert res["volumetric_closure_passed"] is True
    assert res["interpenetration_count"] == 0
    assert res["strata_valid"] is True


def test_3d_strata_interpenetration_detected_when_floors_overlap():
    """
    Benchmark B3.4 Failure Test: Overlapping floor levels trigger invalid strata alert.
    """
    footprint_area = 150.0
    floor_1 = {"z_min": 0.0, "z_max": 3.2, "area": footprint_area, "volume": 150.0 * 3.2}
    floor_2 = {"z_min": 3.0, "z_max": 6.0, "area": footprint_area, "volume": 150.0 * 3.0}  # Overlaps 0.2m
    
    res = Cadastre3DVerifier.verify_strata_enclosure([floor_1, floor_2], total_building_envelope_volume=150.0 * 6.0)
    assert res["interpenetration_count"] == 1
    assert res["strata_valid"] is False


# ==============================================================================
# 6. MERKLE PROVENANCE & LEDGER INTEGRITY BENCHMARK (MeitY / NIC)
# ==============================================================================

def test_merkle_provenance_chain_integrity():
    """
    Benchmark B7.1: SHA3-256 Merkle Hash Chain Integrity.
    """
    ulpin = "27010410010002"
    h0 = "0" * 64
    
    block1_hash = MerkleProvenanceEngine.compute_mutation_hash(
        ulpin, "2026-09-06T10:00:00Z", "Officer_1", "010300000001000000", h0
    )
    block2_hash = MerkleProvenanceEngine.compute_mutation_hash(
        ulpin, "2026-09-06T11:00:00Z", "Officer_2", "010300000001000000", block1_hash
    )
    
    chain = [
        {"ulpin": ulpin, "timestamp": "2026-09-06T10:00:00Z", "officer_id": "Officer_1", "geom_wkb": "010300000001000000", "hash": block1_hash},
        {"ulpin": ulpin, "timestamp": "2026-09-06T11:00:00Z", "officer_id": "Officer_2", "geom_wkb": "010300000001000000", "hash": block2_hash},
    ]
    
    assert MerkleProvenanceEngine.verify_merkle_chain(chain) is True
    
    # Tamper with block 1
    chain[0]["hash"] = "tampered_hash_value"
    assert MerkleProvenanceEngine.verify_merkle_chain(chain) is False


# ==============================================================================
# 7. END-TO-END 7 STATUTORY QUALITY GATES ADJUDICATION DOSSIER TEST
# ==============================================================================

def test_7_statutory_adjudication_quality_gates_and_dossier(surveyed_icps_and_drone_points):
    """
    Benchmark Section 6: Full 7 Quality Gates orchestration & JSON schema verification.
    """
    orchestrator = StatutoryQualityGateOrchestrator()
    
    parcel_context = {
        "ulpin": "27010410010002",
        "khasra_no": "118/2",
        "state": "Maharashtra",
        "district": "Pune",
        "taluka": "Haveli",
        "village": "Sadashiv Peth",
        "legal_area_sqm": 1250.00,
        "prev_hash": "0" * 64,
    }
    
    # Compliant parcel geometry (1249.72 m2)
    parcel_poly = Polygon([(100, 100), (135.35, 100), (135.35, 135.35), (100, 135.35), (100, 100)])
    
    # Adjoining parcels with zero overlap
    adj_parcels = [
        Polygon([(135.35, 100), (170, 100), (170, 135.35), (135.35, 135.35), (135.35, 100)])
    ]
    
    statutory_layers = {
        "dp_road_centerline": LineString([(0, 200), (300, 200)]),  # 65m away (>12m)
        "dp_road_width": 24.0,
        "gas_pipeline": LineString([(0, 50), (300, 50)]),           # 50m away (>5m)
        "waterbody_line": LineString([(0, 0), (300, 0)]),           # 100m away (>9m)
        "railway_track": LineString([(0, 500), (300, 500)]),        # 365m away (>30m)
    }
    
    ocr_metrics = {"cer": 0.012, "wer": 0.028}
    covariance_semi_major_m = 0.082  # <= 0.15m
    
    dossier = orchestrator.evaluate_gates_and_compile_dossier(
        parcel_context=parcel_context,
        survey_icps=surveyed_icps_and_drone_points,
        parcel_poly=parcel_poly,
        adjoining_parcels=adj_parcels,
        statutory_layers=statutory_layers,
        ocr_metrics=ocr_metrics,
        covariance_semi_major_m=covariance_semi_major_m,
    )
    
    # Verify Schema & Gates
    assert dossier["$schema"] == "https://naksha.dolr.gov.in/schemas/adjudication_dossier_v1.json"
    assert dossier["ulpin"] == "27010410010002"
    assert dossier["all_quality_gates_cleared"] is True
    assert len(dossier["quality_gates"]) == 7
    
    for gate_name, gate_info in dossier["quality_gates"].items():
        assert gate_info["passed"] is True, f"{gate_name} failed unexpectedly"
        
    assert "CLEAR" in dossier["inter_agency_clearances"]["pmc_dp_road_row"]
    assert "CLEAR" in dossier["inter_agency_clearances"]["mngl_city_gas_pipeline"]
    assert "CLEAR" in dossier["inter_agency_clearances"]["jal_shakti_nala_buffer"]
    assert "CLEAR" in dossier["inter_agency_clearances"]["railway_setback_zone"]
    assert len(dossier["cryptographic_provenance"]["merkle_root_hash"]) == 64
