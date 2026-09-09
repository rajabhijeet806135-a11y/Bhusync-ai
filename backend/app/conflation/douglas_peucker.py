"""
BhuSynch AI — Douglas-Peucker + Angle Regularizer
====================================================
Subsystem 3: GeoAI Edge Conflation

Simplifies SAM-Geo extracted boundaries while preserving
building corners through angle regularization.

Pipeline: [SAM-Geo ViT-H] → [Douglas-Peucker + Angle Regularizer] → [GIN Fréchet]
"""

import math
from typing import List, Optional, Tuple

import numpy as np


class DouglasPeuckerRegularizer:
    """
    Douglas-Peucker polyline simplification with angle regularization.

    After SAM-Geo produces pixel-level boundary masks, contours are
    extracted and simplified. The angle regularizer snaps near-right
    angles to exact 90° to produce clean cadastral boundaries.
    """

    def __init__(self, epsilon: float = 0.5, angle_threshold: float = 15.0):
        self.epsilon = epsilon
        self.angle_threshold = angle_threshold

    def simplify(self, points: np.ndarray, epsilon: Optional[float] = None) -> np.ndarray:
        eps = self.epsilon if epsilon is None else epsilon
        return self._simplify_algo(points, eps)

    def simplify_and_regularize(
        self,
        points: np.ndarray,
        epsilon: Optional[float] = None,
        angle_threshold_deg: Optional[float] = None,
    ) -> np.ndarray:
        eps = self.epsilon if epsilon is None else epsilon
        athresh = self.angle_threshold if angle_threshold_deg is None else angle_threshold_deg
        simplified = self._simplify_algo(points, eps)
        return self.regularize_angles(simplified, athresh)

    @staticmethod
    def _simplify_algo(
        points: np.ndarray,
        epsilon: float = 0.5,
    ) -> np.ndarray:
        """
        Douglas-Peucker polyline simplification.
        """
        if len(points) <= 2:
            return points.copy()

        # Find point with maximum distance from line segment
        start, end = points[0], points[-1]
        line_vec = end - start
        line_len = np.linalg.norm(line_vec)

        if line_len < 1e-10:
            # Degenerate line segment
            dists = np.linalg.norm(points - start, axis=1)
            max_idx = int(np.argmax(dists))
            max_dist = float(dists[max_idx])
        else:
            line_unit = line_vec / line_len
            vecs = points - start
            projections = np.dot(vecs, line_unit)
            closest = start + np.outer(projections, line_unit)
            dists = np.linalg.norm(points - closest, axis=1)
            max_idx = int(np.argmax(dists))
            max_dist = float(dists[max_idx])

        if max_dist > epsilon:
            # Recursive divide and conquer
            left = DouglasPeuckerRegularizer._simplify_algo(points[: max_idx + 1], epsilon)
            right = DouglasPeuckerRegularizer._simplify_algo(points[max_idx:], epsilon)
            return np.vstack([left[:-1], right])
        else:
            return np.array([start, end])

    @staticmethod
    def regularize_angles(
        points: np.ndarray,
        angle_threshold_deg: float = 15.0,
        target_angles: Optional[List[float]] = None,
    ) -> np.ndarray:
        """
        Snap near-orthogonal angles to exact 90° / 180° / 270°.
        Cadastral parcels predominantly have right-angled corners.
        """
        if target_angles is None:
            target_angles = [90.0, 180.0, 270.0]

        if len(points) < 3:
            return points.copy()

        result = points.copy()
        n = len(result)
        is_closed = np.allclose(result[0], result[-1])
        limit = n - 1 if is_closed else n - 2

        for i in range(limit):
            prev_idx = (i - 1) % (n - 1) if is_closed else max(0, i - 1)
            curr_idx = i
            next_idx = (i + 1) % (n - 1) if is_closed else i + 1

            p_prev = result[prev_idx]
            p_curr = result[curr_idx]
            p_next = result[next_idx]

            v1 = p_prev - p_curr
            v2 = p_next - p_curr

            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            angle_deg = math.degrees(math.acos(cos_angle))

            for target in target_angles:
                if abs(angle_deg - target) < angle_threshold_deg:
                    target_rad = math.radians(target)
                    v1_unit = v1 / (np.linalg.norm(v1) + 1e-10)
                    cos_t = math.cos(target_rad)
                    sin_t = math.sin(target_rad)
                    v2_snapped = np.array([
                        v1_unit[0] * cos_t - v1_unit[1] * sin_t,
                        v1_unit[0] * sin_t + v1_unit[1] * cos_t,
                    ])
                    v2_len = np.linalg.norm(v2)
                    result[next_idx] = result[i] + v2_snapped * v2_len
                    break

        return result


DouglasPeuckerSimplifier = DouglasPeuckerRegularizer
