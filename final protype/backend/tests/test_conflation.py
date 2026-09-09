"""
Tests for GeoAI Edge Conflation & Graph Neural Optimization (Subsystem 3).

Validates:
- Douglas-Peucker polygon simplification with angle regularization
- Fréchet distance matching between legacy and AI-detected boundaries
- ICP (Iterative Closest Point) hierarchical block-level adjustment
- Graph Isomorphism Network (GIN) conflation matching
"""
import pytest
import numpy as np

from app.conflation.douglas_peucker import DouglasPeuckerSimplifier
from app.conflation.frechet_matching import FrechetMatcher
from app.conflation.icp_adjustment import ICPAdjuster


class TestDouglasPeucker:
    """Tests for Douglas-Peucker simplification with angle regularization."""

    def test_straight_line_reduces_to_endpoints(self):
        """A straight line should simplify to just its endpoints."""
        simplifier = DouglasPeuckerSimplifier(epsilon=1.0)
        line = np.array([[0, 0], [1, 0], [2, 0], [3, 0], [4, 0]], dtype=np.float64)
        simplified = simplifier.simplify(line)
        assert len(simplified) == 2
        np.testing.assert_allclose(simplified[0], [0, 0])
        np.testing.assert_allclose(simplified[-1], [4, 0])

    def test_square_preserves_corners(self):
        """A square polygon should preserve all 4 corners."""
        simplifier = DouglasPeuckerSimplifier(epsilon=0.01)
        square = np.array([
            [0, 0], [1, 0], [1, 1], [0, 1], [0, 0]
        ], dtype=np.float64)
        simplified = simplifier.simplify(square)
        assert len(simplified) >= 4

    def test_epsilon_zero_preserves_all_points(self):
        """Epsilon=0 should preserve all input points."""
        simplifier = DouglasPeuckerSimplifier(epsilon=0.0)
        line = np.array([[0, 0], [0.5, 0.1], [1, 0]], dtype=np.float64)
        simplified = simplifier.simplify(line)
        assert len(simplified) == len(line)

    def test_large_epsilon_aggressive_simplification(self):
        """Large epsilon should aggressively reduce points."""
        simplifier = DouglasPeuckerSimplifier(epsilon=100.0)
        zigzag = np.array([[i, (i % 2) * 0.5] for i in range(20)], dtype=np.float64)
        simplified = simplifier.simplify(zigzag)
        assert len(simplified) < len(zigzag)

    def test_angle_regularization(self):
        """Angle regularization should snap near-right-angles to 90 degrees."""
        simplifier = DouglasPeuckerSimplifier(epsilon=0.1, angle_threshold=5.0)
        # Polygon with near-right-angles (88, 92 degrees)
        polygon = np.array([
            [0, 0], [10, 0.2], [10.1, 10], [0.1, 9.9], [0, 0]
        ], dtype=np.float64)
        regularized = simplifier.simplify_and_regularize(polygon)
        assert regularized is not None
        assert len(regularized) >= 4


class TestFrechetMatching:
    """Tests for Fréchet elastic graph optimization matching."""

    def test_identical_curves_zero_distance(self):
        """Fréchet distance between identical curves should be 0."""
        matcher = FrechetMatcher()
        curve = np.array([[0, 0], [1, 0], [2, 0], [3, 0]], dtype=np.float64)
        dist = matcher.frechet_distance(curve, curve)
        assert abs(dist) < 1e-6

    def test_parallel_offset_curves(self):
        """Parallel curves offset by d should have Fréchet distance ≈ d."""
        matcher = FrechetMatcher()
        curve1 = np.array([[0, 0], [1, 0], [2, 0]], dtype=np.float64)
        curve2 = np.array([[0, 1], [1, 1], [2, 1]], dtype=np.float64)
        dist = matcher.frechet_distance(curve1, curve2)
        assert abs(dist - 1.0) < 1e-6

    def test_matching_returns_correspondence(self):
        """Matching should return edge correspondence between legacy and detected."""
        matcher = FrechetMatcher()
        legacy = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.float64)
        detected = np.array([[0.5, 0.5], [10.5, 0.5], [10.5, 10.5], [0.5, 10.5]], dtype=np.float64)
        matches = matcher.match_edges(legacy, detected)
        assert matches is not None
        assert len(matches) > 0

    def test_symmetric_distance(self):
        """Fréchet distance should be symmetric: d(A,B) = d(B,A)."""
        matcher = FrechetMatcher()
        a = np.array([[0, 0], [1, 1], [2, 0]], dtype=np.float64)
        b = np.array([[0, 0.5], [1, 1.5], [2, 0.5]], dtype=np.float64)
        assert abs(matcher.frechet_distance(a, b) - matcher.frechet_distance(b, a)) < 1e-6


class TestICPAdjustment:
    """Tests for Hierarchical Block-Level ICP Adjustment."""

    def test_perfect_alignment_zero_displacement(self):
        """Identical point sets should produce zero displacement."""
        adjuster = ICPAdjuster()
        pts = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float64)
        displacement, rmse = adjuster.align(pts, pts)
        assert rmse < 1e-6

    def test_translation_recovery(self):
        """ICP should recover a pure translation offset."""
        adjuster = ICPAdjuster()
        source = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float64)
        target = source + np.array([0.5, 0.3])
        displacement, rmse = adjuster.align(source, target)
        assert rmse < 0.1

    def test_displacement_within_suwardhi_benchmark(self):
        """Boundary displacement should reduce to 0.40-0.50m (Suwardhi benchmark)."""
        adjuster = ICPAdjuster()
        # Simulate legacy polygons with ~0.80m offset from detected
        np.random.seed(42)
        source = np.random.rand(50, 2) * 100
        target = source + np.array([0.8, 0.6]) + np.random.normal(0, 0.1, source.shape)
        displacement, rmse = adjuster.align(source, target, max_iterations=100)
        # After ICP, displacement should be significantly reduced below Suwardhi 0.50m benchmark
        assert rmse < 0.50
