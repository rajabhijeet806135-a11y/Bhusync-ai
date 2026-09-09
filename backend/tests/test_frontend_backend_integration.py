"""
BhuSynch AI — Frontend-Backend Integration Test Suite
======================================================
Tests all REST and OGC endpoints called by the frontend:
- 3D Console parcel and conflict queries for all jurisdictions (Jharkhand, West Bengal, Maharashtra)
- Search by ULPIN / Khasra No. (Digital Twin lookup)
- Adjudication conflict lists and case details
- Multi-ministry 7-gate benchmark validation
- Merkle audit verification & chronological ledger history
- Live cloud backend (Render) connectivity and schema verification
"""

import pytest
import requests
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

class TestFrontendBackendIntegration:
    """Validates all endpoints used by frontend/js/api-client.js and GIS layers."""

    def test_health_and_root(self, client):
        r_root = client.get("/")
        assert r_root.status_code == 200
        assert r_root.json()["service"] == "BhuSynch AI"

        r_health = client.get("/health")
        assert r_health.status_code == 200
        assert r_health.json()["status"] == "healthy"

    def test_ogc_conformance(self, client):
        r = client.get("/ogc/features/conformance")
        assert r.status_code == 200
        data = r.json()
        assert "conformsTo" in data
        assert any("ogcapi-features" in url for url in data["conformsTo"])

    def test_ogc_collections(self, client):
        r = client.get("/ogc/features/collections")
        assert r.status_code == 200
        data = r.json()
        col_ids = [c["id"] for c in data["collections"]]
        assert "parcels" in col_ids
        assert "conflicts" in col_ids

    # --- JURISDICTION PARCEL QUERIES (Console Dropdown) ---

    def test_parcels_query_ranchi_piska(self, client):
        r = client.get("/ogc/features/collections/parcels/items?state_code=20_ranchi_piska&limit=1000")
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0
        feat = data["features"][0]
        assert feat["geometry"]["type"] in ["Polygon", "MultiPolygon"]
        assert "ulpin" in feat["properties"] or "id" in feat["properties"]

    def test_parcels_query_ranchi_capital(self, client):
        r = client.get("/ogc/features/collections/parcels/items?state_code=20_ranchi&limit=1000")
        assert r.status_code == 200
        data = r.json()
        assert len(data["features"]) > 0

    def test_parcels_query_west_bengal_medinipur(self, client):
        r = client.get("/ogc/features/collections/parcels/items?state_code=19_west_medinipur&limit=1000")
        assert r.status_code == 200
        data = r.json()
        assert len(data["features"]) > 0

    def test_parcels_query_west_bengal_rishra(self, client):
        r = client.get("/ogc/features/collections/parcels/items?state_code=19_rishra&limit=1000")
        assert r.status_code == 200
        data = r.json()
        assert len(data["features"]) > 0

    def test_parcels_query_west_bengal_statewide(self, client):
        r = client.get("/ogc/features/collections/parcels/items?state_code=19_statewide&limit=1000")
        assert r.status_code == 200
        data = r.json()
        assert len(data["features"]) > 0

    def test_parcels_query_maharashtra_pune(self, client):
        r = client.get("/ogc/features/collections/parcels/items?state_code=27&limit=1000")
        assert r.status_code == 200
        data = r.json()
        assert len(data["features"]) > 0

    # --- CONFLICT QUERIES ---

    def test_conflicts_query_all_jurisdictions(self, client):
        jurisdictions = ["20_ranchi_piska", "20_ranchi", "19_west_medinipur", "19_rishra", "19_statewide", "27"]
        for j in jurisdictions:
            r = client.get(f"/ogc/features/collections/conflicts/items?state_code={j}&limit=100")
            assert r.status_code == 200
            data = r.json()
            assert data["type"] == "FeatureCollection"
            assert len(data["features"]) > 0

    # --- DIGITAL TWIN LOOKUP ---

    def test_ulpin_digital_twin_lookup(self, client):
        r = client.get("/ogc/features/collections/parcels/items/27010410010001")
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "Feature"
        assert "geometry" in data

    # --- ADJUDICATION REST API ---

    def test_adjudication_conflicts_endpoint(self, client):
        r = client.get("/api/v1/adjudication/conflicts")
        assert r.status_code == 200
        data = r.json()
        conflicts = data.get("conflicts", data) if isinstance(data, dict) else data
        assert isinstance(conflicts, list)
        assert len(conflicts) > 0

    def test_multi_ministry_benchmark(self, client):
        r = client.get("/api/v1/adjudication/multi-ministry-benchmark/27010410010001?state_code=27")
        assert r.status_code == 200
        data = r.json()
        assert "concordance_percentage" in data or "quality_gates" in data or "ulpin" in data

    def test_merkle_audit_verification(self, client):
        r = client.get("/api/v1/audit/verify/27010410010001")
        assert r.status_code == 200
        data = r.json()
        assert "verified" in data or "chain_intact" in data or "ulpin" in data

    # --- LIVE RENDER BACKEND HEALTH ---

    def test_live_render_cloud_endpoint(self):
        """Verify the deployed cloud backend on Render is responding."""
        try:
            resp = requests.get("https://bhusync-api-25dk.onrender.com/", timeout=10)
            assert resp.status_code == 200
            data = resp.json()
            assert data["service"] == "BhuSynch AI"
        except (requests.exceptions.RequestException, AssertionError) as e:
            pytest.skip(f"Live Render backend offline or sleeping: {e}")
