"""
Tests for Subsystem 1: Automated Geodesy & Deep Feature Co-Registration.

Validates:
- 7-Parameter Helmert transformation (Kalianpur 1830 → WGS84 / EPSG:7755)
- Thin-Plate Spline (TPS) elastic deformation correction
- CORS constrained least-squares adjustment
- Datum shift formulations
"""
import math
import pytest
import numpy as np

# ---------------------------------------------------------------------------
# Import modules under test
# ---------------------------------------------------------------------------
from app.geodesy.helmert import HelmertTransformer
from app.geodesy.thin_plate_spline import ThinPlateSpline
from app.geodesy.cors_adjustment import CORSLeastSquaresAdjuster
from app.geodesy.datum_shift import DatumShiftEngine


# ===================================================================
# Helmert 7-Parameter Transformation Tests
# ===================================================================

class TestHelmertTransformer:
    """Tests for the 7-parameter Helmert (similarity) transformation."""

    def setup_method(self):
        """Set up standard Kalianpur 1830 → WGS84 parameters."""
        self.transformer = HelmertTransformer(
            dx=295.0, dy=736.0, dz=257.0,
            rx=0.0, ry=0.0, rz=0.0,
            scale_ppm=-0.0
        )

    def test_identity_when_no_params(self):
        """Zero parameters should return input coordinates unchanged."""
        identity = HelmertTransformer(
            dx=0, dy=0, dz=0, rx=0, ry=0, rz=0, scale_ppm=0
        )
        x, y, z = 1000000.0, 2000000.0, 3000000.0
        xo, yo, zo = identity.transform(x, y, z)
        assert abs(xo - x) < 1e-6
        assert abs(yo - y) < 1e-6
        assert abs(zo - z) < 1e-6

    def test_translation_only(self):
        """Pure translation should add dx, dy, dz to input coords."""
        t = HelmertTransformer(dx=100, dy=200, dz=300, rx=0, ry=0, rz=0, scale_ppm=0)
        xo, yo, zo = t.transform(0, 0, 0)
        assert abs(xo - 100.0) < 1e-6
        assert abs(yo - 200.0) < 1e-6
        assert abs(zo - 300.0) < 1e-6

    def test_kalianpur_to_wgs84_produces_valid_shift(self):
        """Transformation of a known Everest coord should shift significantly."""
        x_ev, y_ev, z_ev = 1234567.0, 2345678.0, 3456789.0
        xo, yo, zo = self.transformer.transform(x_ev, y_ev, z_ev)
        # After transformation, coords should be shifted by approx dx, dy, dz
        assert abs(xo - x_ev - 295.0) < 100.0
        assert abs(yo - y_ev - 736.0) < 100.0
        assert abs(zo - z_ev - 257.0) < 100.0

    def test_inverse_transform_roundtrip(self):
        """Forward + inverse should return to original coordinates."""
        x, y, z = 1000000.0, 2000000.0, 3000000.0
        xf, yf, zf = self.transformer.transform(x, y, z)
        xi, yi, zi = self.transformer.inverse_transform(xf, yf, zf)
        assert abs(xi - x) < 0.01
        assert abs(yi - y) < 0.01
        assert abs(zi - z) < 0.01

    def test_scale_factor_effect(self):
        """Non-zero scale ppm should change output magnitude."""
        t_scaled = HelmertTransformer(
            dx=0, dy=0, dz=0, rx=0, ry=0, rz=0, scale_ppm=1.0
        )
        x, y, z = 1000000.0, 0.0, 0.0
        xo, yo, zo = t_scaled.transform(x, y, z)
        # 1 ppm on 1e6 meters = 1 meter difference
        assert abs(xo - 1000001.0) < 0.01


# ===================================================================
# Thin-Plate Spline Tests
# ===================================================================

class TestThinPlateSpline:
    """Tests for TPS elastic deformation correction."""

    def test_interpolation_exact_at_control_points(self):
        """TPS should pass exactly through control points."""
        src = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], dtype=np.float64)
        dst = np.array([[0.1, 0.1], [1.1, 0.1], [0.1, 1.1], [1.1, 1.1]], dtype=np.float64)
        tps = ThinPlateSpline(lambda_reg=0.0)
        tps.fit(src, dst)
        result = tps.transform(src)
        np.testing.assert_allclose(result, dst, atol=1e-6)

    def test_identity_mapping(self):
        """When source == destination, TPS should be identity."""
        pts = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], dtype=np.float64)
        tps = ThinPlateSpline(lambda_reg=0.0)
        tps.fit(pts, pts)
        result = tps.transform(pts)
        np.testing.assert_allclose(result, pts, atol=1e-6)

    def test_regularization_smoothing(self):
        """Higher lambda should produce smoother (less exact) interpolation."""
        src = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], dtype=np.float64)
        dst = np.array([[0.5, 0.5], [1.5, 0.5], [0.5, 1.5], [1.5, 1.5]], dtype=np.float64)
        tps_exact = ThinPlateSpline(lambda_reg=0.0)
        tps_exact.fit(src, dst)
        tps_smooth = ThinPlateSpline(lambda_reg=100.0)
        tps_smooth.fit(src, dst)
        err_exact = np.linalg.norm(tps_exact.transform(src) - dst)
        err_smooth = np.linalg.norm(tps_smooth.transform(src) - dst)
        assert err_smooth >= err_exact


# ===================================================================
# CORS Least-Squares Adjustment Tests
# ===================================================================

class TestCORSAdjustment:
    """Tests for CORS constrained least-squares adjustment."""

    def test_perfect_observations_zero_residuals(self):
        """Perfect observations should yield zero residuals."""
        adjuster = CORSLeastSquaresAdjuster()
        # Simple 2D translation: observed = actual + [10, 20]
        design_matrix = np.eye(2)
        observations = np.array([10.0, 20.0])
        weights = np.eye(2)
        params, rmse, residuals = adjuster.adjust(design_matrix, observations, weights)
        np.testing.assert_allclose(params, [10.0, 20.0], atol=1e-6)
        assert rmse < 1e-6

    def test_overdetermined_system(self):
        """Overdetermined system should produce valid least-squares solution."""
        adjuster = CORSLeastSquaresAdjuster()
        A = np.array([[1, 0], [0, 1], [1, 1]], dtype=np.float64)
        L = np.array([10.0, 20.0, 30.0])
        P = np.eye(3)
        params, rmse, residuals = adjuster.adjust(A, L, P)
        # x̂ = (A^T P A)^(-1) A^T P L
        assert len(params) == 2
        assert rmse >= 0.0

    def test_rmse_formula(self):
        """RMSE should follow √(Σv²/(n-m)) formula."""
        adjuster = CORSLeastSquaresAdjuster()
        A = np.array([[1], [1], [1]], dtype=np.float64)
        L = np.array([10.0, 11.0, 12.0])
        P = np.eye(3)
        params, rmse, residuals = adjuster.adjust(A, L, P)
        # Manual: mean=11, residuals=[-1, 0, 1], sum_sq=2, rmse=√(2/(3-1))=1.0
        assert abs(rmse - 1.0) < 1e-6


# ===================================================================
# Datum Shift Engine Tests
# ===================================================================

class TestDatumShift:
    """Tests for Kalianpur 1830 → WGS84 datum shift."""

    def test_geodetic_to_cartesian_roundtrip(self):
        """Geographic ↔ Cartesian conversion roundtrip must be lossless."""
        engine = DatumShiftEngine()
        lat, lon, h = 28.6139, 77.2090, 200.0  # New Delhi
        x, y, z = engine.geodetic_to_cartesian(lat, lon, h)
        lat2, lon2, h2 = engine.cartesian_to_geodetic(x, y, z)
        assert abs(lat2 - lat) < 1e-8
        assert abs(lon2 - lon) < 1e-8
        assert abs(h2 - h) < 0.01

    def test_output_is_wgs84(self):
        """Output of datum shift should be valid WGS84 coordinates."""
        engine = DatumShiftEngine()
        lat_ev, lon_ev = 28.5, 77.0
        lat_wgs, lon_wgs = engine.shift_kalianpur_to_wgs84(lat_ev, lon_ev, 0.0)
        # WGS84 lat should be in valid range
        assert -90 <= lat_wgs <= 90
        assert -180 <= lon_wgs <= 180
        # Should be close to original (within a few hundred meters → ~0.01 degrees)
        assert abs(lat_wgs - lat_ev) < 0.05
        assert abs(lon_wgs - lon_ev) < 0.05
