"""
Tests for ULPIN (Bhu-Aadhaar) 14-Character Centroid Encoding.

Validates:
- Centroid computation from polygon geometry
- 14-character ULPIN format generation
- State code encoding
- Area computation in m²
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from app.services.ulpin_service import ULPINService


class TestULPINService:
    """Tests for the ULPIN 14-character encoding service."""

    def setup_method(self):
        """Set up ULPIN service with mocked DB session."""
        self.service = ULPINService()

    def test_centroid_computation_square(self):
        """Centroid of a square should be its geometric center."""
        # Square: (0,0), (1,0), (1,1), (0,1)
        coords = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
        cx, cy = self.service.compute_centroid(coords)
        assert abs(cx - 0.5) < 1e-6
        assert abs(cy - 0.5) < 1e-6

    def test_centroid_computation_triangle(self):
        """Centroid of a triangle should be average of vertices."""
        coords = [(0, 0), (3, 0), (0, 3), (0, 0)]
        cx, cy = self.service.compute_centroid(coords)
        assert abs(cx - 1.0) < 1e-6
        assert abs(cy - 1.0) < 1e-6

    def test_ulpin_length_is_14_characters(self):
        """Generated ULPIN must be exactly 14 characters."""
        ulpin = self.service.generate_ulpin(
            lat=28.6139, lon=77.2090,
            area_sqm=5000.0, state_code="09"
        )
        assert len(ulpin) == 14

    def test_ulpin_contains_state_code(self):
        """ULPIN should embed the state code."""
        ulpin = self.service.generate_ulpin(
            lat=28.6139, lon=77.2090,
            area_sqm=5000.0, state_code="09"
        )
        assert ulpin[:2] == "09"

    def test_different_coords_produce_different_ulpins(self):
        """Different locations must produce unique ULPINs."""
        ulpin1 = self.service.generate_ulpin(
            lat=28.6139, lon=77.2090, area_sqm=5000.0, state_code="09"
        )
        ulpin2 = self.service.generate_ulpin(
            lat=19.0760, lon=72.8777, area_sqm=5000.0, state_code="27"
        )
        assert ulpin1 != ulpin2

    def test_area_conversion_bigha_to_sqm(self):
        """Vernacular area unit conversion: Bigha → m²."""
        sqm = self.service.convert_area_to_sqm(1.0, "bigha")
        # 1 Bigha (standard) ≈ 2529.285 m²
        assert 2000 < sqm < 3000

    def test_area_conversion_gunta_to_sqm(self):
        """Vernacular area unit conversion: Gunta → m²."""
        sqm = self.service.convert_area_to_sqm(1.0, "gunta")
        # 1 Gunta ≈ 101.17 m²
        assert 90 < sqm < 115

    def test_area_conversion_katha_to_sqm(self):
        """Vernacular area unit conversion: Katha → m²."""
        sqm = self.service.convert_area_to_sqm(1.0, "katha")
        # 1 Katha ≈ 126.44 m² (varies by state)
        assert 100 < sqm < 200

    def test_area_conversion_biswa_to_sqm(self):
        """Vernacular area unit conversion: Biswa → m²."""
        sqm = self.service.convert_area_to_sqm(1.0, "biswa")
        # 1 Biswa ≈ 125 m²
        assert 100 < sqm < 200

    def test_polygon_area_sqm(self):
        """Polygon area calculation in square meters."""
        # 100m x 100m square
        coords = [
            (0, 0), (0.0009, 0), (0.0009, 0.0009), (0, 0.0009), (0, 0)
        ]
        area = self.service.compute_polygon_area_sqm(coords, lat_ref=28.6)
        assert area > 0

    def test_ulpin_alphanumeric(self):
        """ULPIN must only contain alphanumeric characters."""
        ulpin = self.service.generate_ulpin(
            lat=28.6139, lon=77.2090, area_sqm=5000.0, state_code="09"
        )
        assert ulpin.isalnum()
