"""
BhuSynch AI — Hierarchical Block-Level ICP Adjustment
=======================================================
Subsystem 3: GeoAI Edge Conflation

Iterative Closest Point (ICP) algorithm for block-level
geometric alignment. Suwardhi Benchmark: reduces displacement
from 0.80m down to 0.40m–0.50m across block clusters (Section 2.3).
"""

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


@dataclass
class ICPResult:
    """Result of ICP alignment."""
    rotation: np.ndarray        # 2x2 rotation matrix
    translation: np.ndarray     # 2D translation vector
    scale: float                # Scale factor
    initial_rmse: float         # RMSE before ICP
    final_rmse: float           # RMSE after ICP
    iterations: int             # Number of iterations to converge
    correspondences: np.ndarray  # Nx2 index pairs

    def __iter__(self):
        # Allows unpacking: displacement, rmse = result
        yield self.translation
        yield self.final_rmse


class ICPAdjustment:
    """
    Hierarchical Block-Level ICP Adjustment.
    Applies ICP at block-cluster level to achieve sub-meter alignment accuracy.
    """

    def __init__(self, max_iterations: int = 50, tolerance: float = 1e-5):
        self.max_iterations = max_iterations
        self.tolerance = tolerance

    def align(
        self,
        source: np.ndarray,
        target: np.ndarray,
        max_iterations: Optional[int] = None,
        tolerance: Optional[float] = None,
        max_distance: float = 100.0,
    ) -> ICPResult:
        max_iter = self.max_iterations if max_iterations is None else max_iterations
        tol = self.tolerance if tolerance is None else tolerance
        return self._align_core(source, target, max_iter, tol, max_distance)

    @classmethod
    def align_points(
        cls,
        source: np.ndarray,
        target: np.ndarray,
        max_iterations: int = 50,
        tolerance: float = 1e-5,
        max_distance: float = 100.0,
    ) -> ICPResult:
        return cls._align_core(source, target, max_iterations, tolerance, max_distance)

    @staticmethod
    def _align_core(
        source: np.ndarray,
        target: np.ndarray,
        max_iterations: int = 50,
        tolerance: float = 1e-5,
        max_distance: float = 100.0,
    ) -> ICPResult:
        src = np.array(source, dtype=np.float64).copy()
        tgt = np.array(target, dtype=np.float64).copy()

        initial_dists = np.linalg.norm(src[:, None, :] - tgt[None, :, :], axis=2)
        initial_rmse = float(np.sqrt(np.mean(np.min(initial_dists, axis=1) ** 2)))

        accum_R = np.eye(2)
        accum_t = np.zeros(2)
        prev_rmse = initial_rmse
        iterations_run = 0
        correspondences = np.empty((0, 2), dtype=int)

        for iteration in range(max_iterations):
            iterations_run = iteration + 1
            dists = np.linalg.norm(src[:, None, :] - tgt[None, :, :], axis=2)
            match_idx = np.argmin(dists, axis=1)
            min_dists = np.min(dists, axis=1)

            valid_mask = min_dists <= max_distance
            if np.sum(valid_mask) < 3:
                break

            src_matched = src[valid_mask]
            tgt_matched = tgt[match_idx[valid_mask]]
            correspondences = np.column_stack([np.where(valid_mask)[0], match_idx[valid_mask]])

            src_c = np.mean(src_matched, axis=0)
            tgt_c = np.mean(tgt_matched, axis=0)

            H = (src_matched - src_c).T @ (tgt_matched - tgt_c)
            U, S_vals, Vt = np.linalg.svd(H)
            R = Vt.T @ U.T
            if np.linalg.det(R) < 0:
                Vt[-1, :] *= -1
                R = Vt.T @ U.T

            t = tgt_c - (src_c @ R.T)

            src = src @ R.T + t
            accum_R = R @ accum_R
            accum_t = accum_t @ R.T + t

            current_dists = np.linalg.norm(src[:, None, :] - tgt[None, :, :], axis=2)
            current_rmse = float(np.sqrt(np.mean(np.min(current_dists, axis=1) ** 2)))

            if abs(prev_rmse - current_rmse) < tolerance:
                break
            prev_rmse = current_rmse

        final_dists = np.linalg.norm(src[:, None, :] - tgt[None, :, :], axis=2)
        final_rmse = float(np.sqrt(np.mean(np.min(final_dists, axis=1) ** 2)))

        return ICPResult(
            rotation=accum_R,
            translation=accum_t,
            scale=1.0,
            initial_rmse=initial_rmse,
            final_rmse=final_rmse,
            iterations=iterations_run,
            correspondences=correspondences,
        )


ICPAdjuster = ICPAdjustment
