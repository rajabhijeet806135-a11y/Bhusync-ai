"""
Tests for OGC API & REST Endpoints — Features, Processes, Tiles, Adjudication, Audit.
===================================================================================
Validates:
- Health and root discovery
- OGC API Features (Part 1 & 2): Conformance, Collections, Items, CRS reprojection, Digital Twins
- OGC API Processes (Async/Sync): Process list, Description, Execution, Status polling
- OGC API Tiles: TileSet metadata, TileJSON, MVT vector tile responses
- Adjudication REST API: Conflict queue, Dispute details, DSC officer decisions, Dossiers
- Audit REST API: SHA3-256 Merkle chain verification & chronological mutation history
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


# =====================================================================
# 1. Health & Root Endpoint Tests
# =====================================================================

class TestHealthEndpoints:
    """Tests for health check and root endpoints."""

    def test_health_endpoint_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "BhuSynch AI"
        assert data["problem_statement"] == "SIH 26013"


# =====================================================================
# 2. OGC Features API Tests (Part 1 & Part 2)
# =====================================================================

class TestOGCFeaturesAPI:
    """Tests for OGC API Features endpoints."""

    def test_get_conformance(self, client):
        """GET /ogc/features/conformance should return OGC conformance classes."""
        response = client.get("/ogc/features/conformance")
        assert response.status_code == 200
        data = response.json()
        assert "conformsTo" in data
        assert any("conf/core" in c for c in data["conformsTo"])
        assert any("conf/geojson" in c for c in data["conformsTo"])
        assert any("conf/crs" in c for c in data["conformsTo"])

    def test_get_collections(self, client):
        """GET /ogc/features/collections should list parcels and conflicts."""
        response = client.get("/ogc/features/collections")
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
        collection_ids = [c["id"] for c in data["collections"]]
        assert "parcels" in collection_ids
        assert "conflicts" in collection_ids

    def test_get_collection_info(self, client):
        """GET /ogc/features/collections/parcels returns detailed metadata."""
        response = client.get("/ogc/features/collections/parcels")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "parcels"
        assert "extent" in data
        assert "crs" in data

    def test_get_parcels_items_with_geometry(self, client):
        """GET /ogc/features/collections/parcels/items should return valid GeoJSON features with real geometry."""
        response = client.get("/ogc/features/collections/parcels/items?crs=EPSG:4326")
        assert response.status_code == 200
        data = response.json()
        assert data.get("type") == "FeatureCollection"
        assert len(data.get("features", [])) > 0

        # Verify first feature geometry is valid GeoJSON Polygon
        first_feature = data["features"][0]
        assert first_feature["type"] == "Feature"
        geom = first_feature.get("geometry")
        assert geom is not None, "Geometry must not be null"
        assert geom["type"] in ["Polygon", "MultiPolygon"]
        coords = geom["coordinates"]
        assert len(coords) > 0

    def test_parcels_crs_transformation(self, client):
        """Verify coordinates reproject properly between EPSG:4326 (lon/lat) and EPSG:7755 (meters)."""
        r_4326 = client.get("/ogc/features/collections/parcels/items?crs=EPSG:4326")
        r_7755 = client.get("/ogc/features/collections/parcels/items?crs=EPSG:7755")

        assert r_4326.status_code == 200
        assert r_7755.status_code == 200

        feat_4326 = r_4326.json()["features"][0]
        feat_7755 = r_7755.json()["features"][0]

        pt_4326 = feat_4326["geometry"]["coordinates"][0][0]
        pt_7755 = feat_7755["geometry"]["coordinates"][0][0]

        # WGS84 coordinates in Pune are around lon=73.85, lat=18.52
        assert 70.0 < pt_4326[0] < 80.0
        assert 15.0 < pt_4326[1] < 25.0

        # EPSG:7755 (India LCC) coordinates are in projected meters (millions)
        assert pt_7755[0] > 1000000
        assert pt_7755[1] > 1000000

    def test_get_parcel_digital_twin_by_ulpin(self, client):
        """GET /ogc/features/collections/parcels/items/{ulpin} returns Digital Twin."""
        response = client.get("/ogc/features/collections/parcels/items/27010410010001")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "Feature"
        assert data["properties"]["ulpin"] == "27010410010001"
        assert data["geometry"] is not None

    def test_invalid_collection_returns_404(self, client):
        response = client.get("/ogc/features/collections/nonexistent_collection")
        assert response.status_code == 404


# =====================================================================
# 3. OGC Processes API Tests
# =====================================================================

class TestOGCProcessesAPI:
    """Tests for OGC API Processes endpoints."""

    def test_list_processes(self, client):
        """GET /ogc/processes should list available workflows."""
        response = client.get("/ogc/processes")
        assert response.status_code == 200
        data = response.json()
        assert "processes" in data
        p_ids = [p["id"] for p in data["processes"]]
        assert "georeference" in p_ids
        assert "conflation" in p_ids
        assert "change_detection" in p_ids

    def test_describe_process(self, client):
        """GET /ogc/processes/georeference returns schema and inputs."""
        response = client.get("/ogc/processes/georeference")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "georeference"
        assert "inputs" in data

    def test_execute_georeference_process(self, client):
        """POST /ogc/processes/georeference/execution queues async job."""
        payload = {
            "inputs": {
                "sajra_path": "sajra_pune_ward14.tif",
                "reference_ori_path": "drone_ori_5cm.tif",
            }
        }
        response = client.post("/ogc/processes/georeference/execution", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "accepted"
        assert "job_id" in data or "jobID" in data

        job_id = data.get("job_id") or data.get("jobID")
        # Check job status
        status_resp = client.get(f"/ogc/processes/georeference/jobs/{job_id}")
        assert status_resp.status_code == 200


# =====================================================================
# 4. OGC Tiles API Tests
# =====================================================================

class TestOGCTilesAPI:
    """Tests for OGC API Tiles (MVT) endpoints."""

    def test_list_tilesets(self, client):
        response = client.get("/ogc/tiles")
        assert response.status_code == 200
        data = response.json()
        assert "tilesets" in data

    def test_get_tilejson(self, client):
        response = client.get("/ogc/tiles/parcels")
        assert response.status_code == 200
        data = response.json()
        assert data.get("tilejson") == "3.0.0"
        assert "tiles" in data

    def test_mvt_tile_endpoint_stream(self, client):
        response = client.get("/ogc/tiles/parcels/17/93582/58120.pbf")
        assert response.status_code in [200, 204]
        assert "mapbox-vector-tile" in response.headers.get("content-type", "")


# =====================================================================
# 5. Adjudication & Audit REST API Tests
# =====================================================================

class TestAdjudicationAndAuditAPI:
    """Tests for Three-Truths Adjudication and Merkle Provenance APIs."""

    def test_list_conflicts(self, client):
        response = client.get("/api/v1/adjudication/conflicts")
        assert response.status_code == 200
        data = response.json()
        assert "conflicts" in data
        assert data["count"] >= 0

    def test_adjudicate_conflict_with_dsc(self, client):
        payload = {
            "conflict_id": "CONF-2026-0001",
            "officer_id": "REV-OFF-PUNE-14",
            "decision": "ENFORCEMENT_NOTICE",
            "remarks": "Compound wall encroaches 28.4 m² into PMC 12m DP Road Right-of-Way.",
            "apply_dsc": True,
        }
        response = client.post("/api/v1/adjudication/adjudicate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["dsc_signature"]["is_valid"] is True
        assert "merkle_receipt" in data

    def test_generate_statutory_dossier(self, client):
        payload = {
            "officer_id": "REV-OFF-PUNE-14",
            "include_provenance": True,
            "format": "json",
        }
        response = client.post("/api/v1/adjudication/dossier/27010410010002", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "parcel_summary" in data
        assert "three_truths_analysis" in data
        assert "provenance_chain" in data

    def test_verify_audit_merkle_chain(self, client):
        response = client.get("/api/v1/audit/verify/27010410010001")
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["chain_length"] >= 1
        assert "chain" in data

    def test_multi_ministry_benchmark_endpoint(self, client):
        response = client.get("/api/v1/adjudication/multi-ministry-benchmark/27010410010002")
        assert response.status_code == 200
        data = response.json()
        assert data["all_quality_gates_cleared"] is True
        assert len(data["quality_gates"]) == 7
        assert "inter_agency_clearances" in data
        assert "geodetic_metrics" in data
        assert data["ulpin"] == "27010410010002"

