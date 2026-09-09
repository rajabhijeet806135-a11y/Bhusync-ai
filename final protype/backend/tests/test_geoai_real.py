"""
BhuSynch AI — GeoAI Real Models Automated Test Suite
======================================================
Validates that all GeoAI models produce authentic mathematical & computer vision outputs
with zero simulated or random placeholders.
"""

import numpy as np
import pytest

from app.geoai.superpoint import SuperPointModel
from app.geoai.lightglue import LightGlueModel
from app.geoai.sam_geo import SAMGeoModel, SAMGeoInput
from app.geoai.changeformer import ChangeFormerModel
from app.geoai.graph_neural import GraphNeuralModel
from app.geoai.trocr_indic import TrOCRIndicModel
from app.geoai.ward_pipeline import WardGeoAIPipeline


def test_superpoint_real_features():
    """Verify SuperPoint extracts genuine corner features and 256D descriptors."""
    model = SuperPointModel()
    model.load()

    # Create synthetic test image with crisp geometric shapes
    img = np.zeros((128, 128, 3), dtype=np.uint8)
    img[20:80, 20:80] = 255  # White square
    img[40:60, 40:60] = 100  # Gray inner square

    result = model(img)
    pred = result.predictions

    assert len(pred.keypoints) > 0, "SuperPoint should detect corners on geometric shapes"
    assert pred.descriptors.shape[1] == 256, "Descriptors must be exactly 256-dimensional"
    assert np.all(pred.keypoints >= 0) and np.all(pred.keypoints <= 128), "Keypoints must be within image bounds"
    assert pred.scores.min() >= 0.0 and pred.scores.max() <= 1.0, "Scores must be normalized [0, 1]"
    # Verify descriptors are L2 normalized
    norms = np.linalg.norm(pred.descriptors, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3), "Descriptors must be L2 normalized"


def test_lightglue_real_matching():
    """Verify LightGlue performs Sinkhorn matching and RANSAC inlier filtering."""
    sp = SuperPointModel()
    lg = LightGlueModel()
    sp.load()
    lg.load()

    # Create pair of shifted images
    img0 = np.zeros((150, 150, 3), dtype=np.uint8)
    img1 = np.zeros((150, 150, 3), dtype=np.uint8)

    img0[30:90, 30:90] = 255
    img1[35:95, 35:95] = 255  # Shifted by (5, 5)

    res0 = sp(img0)
    res1 = sp(img1)

    lg_input = (
        {
            "keypoints": res0.predictions.keypoints,
            "descriptors": res0.predictions.descriptors,
            "scores": res0.predictions.scores,
        },
        {
            "keypoints": res1.predictions.keypoints,
            "descriptors": res1.predictions.descriptors,
            "scores": res1.predictions.scores,
        }
    )

    match_res = lg(lg_input)
    pred = match_res.predictions

    assert len(pred.matches) > 0, "LightGlue should find matches between shifted geometric shapes"
    assert pred.num_inliers > 0, "RANSAC should identify inliers"
    assert pred.transformation_matrix is not None, "Must estimate transformation matrix"


def test_sam_geo_real_polygonization():
    """Verify SAM-Geo outputs real georeferenced polygon features from 6-channel input."""
    model = SAMGeoModel()
    model.load()

    rgb = np.zeros((100, 100, 3), dtype=np.uint8)
    rgb[20:70, 20:70] = 200  # Building footprint

    dsm = np.zeros((100, 100), dtype=np.float32)
    dtm = np.zeros((100, 100), dtype=np.float32)
    dsm[20:70, 20:70] = 8.5  # 8.5m building height

    sam_in = SAMGeoInput(
        rgb_image=rgb,
        dsm=dsm,
        dtm=dtm,
        geo_transform=(73.8567, 0.00001, 0.0, 18.5204, 0.0, -0.00001),
        crs_epsg=7755,
    )

    result = model(sam_in)
    pred = result.predictions

    assert len(pred.polygons) > 0, "SAM-Geo must extract vectorized polygons"
    first_poly = pred.polygons[0]
    assert first_poly["type"] == "Feature"
    assert first_poly["geometry"]["type"] == "Polygon"
    coords = first_poly["geometry"]["coordinates"][0]
    assert len(coords) >= 4, "Polygon must have at least 4 coordinates (closed ring)"
    assert first_poly["properties"]["area_sqm"] > 0, "Area must be positive"


def test_changeformer_real_differencing():
    """Verify ChangeFormer detects bitemporal differences and classifies floor additions."""
    model = ChangeFormerModel()
    model.load()

    t1 = np.full((100, 100, 3), 50, dtype=np.uint8)
    t2 = t1.copy()
    t2[20:60, 20:60] = 220  # Bright new structure

    dsm1 = np.zeros((100, 100), dtype=np.float32)
    dsm2 = np.zeros((100, 100), dtype=np.float32)
    dsm2[20:60, 20:60] = 6.0  # +6m vertical floor addition

    cf_in = {
        "image_t1": t1,
        "image_t2": t2,
        "dsm_t1": dsm1,
        "dsm_t2": dsm2,
    }

    result = model(cf_in)
    pred = result.predictions

    assert pred.statistics["total_changed_pixels"] > 0, "Must detect changed pixels"
    assert len(pred.change_polygons) > 0, "Must vectorize change zones into GeoJSON"
    first_change = pred.change_polygons[0]
    assert first_change["properties"]["change_type"] in ["FLOOR_ADDITION", "UNAUTHORIZED_CONSTRUCTION"]


def test_graph_neural_conflation():
    """Verify GIN conflation performs Fréchet matching and topological vertex relaxation."""
    model = GraphNeuralModel()
    model.load()

    legacy = [{
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[73.850, 18.520], [73.855, 18.520], [73.855, 18.525], [73.850, 18.525], [73.850, 18.520]]]
        }
    }]

    target = [{
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[73.8502, 18.5201], [73.8552, 18.5201], [73.8552, 18.5251], [73.8502, 18.5251], [73.8502, 18.5201]]]
        }
    }]

    gin_in = {
        "legacy_polygons": legacy,
        "target_polygons": target,
        "crs_epsg": 7755,
    }

    result = model(gin_in)
    pred = result.predictions

    assert len(pred.conflated_polygons) > 0, "Must produce conflated polygons"
    assert pred.mean_displacement >= 0.0, "Displacement must be non-negative"
    assert len(pred.matched_edges) > 0, "Must match boundary edges"


def test_trocr_indic_revenue_parsing():
    """Verify TrOCR Indic parser extracts Khasra numbers and statutory revenue entities."""
    model = TrOCRIndicModel()
    model.load()

    raw_record = {
        "khasra_no": "142/3",
        "khata_no": "275",
        "owner_name_marathi": "राम प्रसाद शर्मा",
        "area_sqm": 387.50,
        "land_type": "बागायत",
    }

    result = model(raw_record)
    pred = result.predictions

    assert pred.parsed_revenue_record["khasra_no"] == "142/3"
    assert pred.parsed_revenue_record["khata_no"] == "275"
    assert "राम" in pred.parsed_revenue_record["owner_name"]
    assert pred.parsed_revenue_record["area_sqm"] == 387.50


def test_ward_pipeline_e2e():
    """Run full end-to-end Ward 14 GeoAI Pipeline."""
    pipeline = WardGeoAIPipeline()
    summary = pipeline.run()

    assert summary["pipeline_status"] == "COMPLETED"
    assert summary["execution_time_seconds"] > 0
    assert summary["matched_gcps_count"] > 0
    assert summary["conflated_parcels_count"] > 0
