"""
BhuSynch AI — Thin-Plate Spline (TPS) Elastic Deformation Correction
======================================================================
Subsystem 1, Step 3: Elastic warp for non-rigid distortion in scanned cloth maps.

Exact formula from Section 2.1:

    E_TPS(f) = Σ_{i=1}^N ‖yᵢ - f(xᵢ)‖² + λ ∬_{ℝ²} ( (∂²f/∂x₁²)² + 2(∂²f/∂x₁∂x₂)² + (∂²f/∂x₂²)² ) dx₁ dx₂

The first term measures data fidelity (GCP residuals).
The second term (with regularization λ) penalizes bending energy,
preventing overfitting to noisy GCP matches.

Pipeline position: SuperPoint → LightGlue → RANSAC → Helmert → [TPS] → CORS
"""

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


@dataclass
class TPSResult:
    """Result of TPS interpolation."""
    affine_params: np.ndarray      # 3x2 affine parameter matrix
    weights: np.ndarray            # Nx2 TPS weights
    control_points: np.ndarray     # Nx2 source control points
    bending_energy: float          # Bending energy of the solution
    lambda_smooth: float           # Regularization parameter used
    rmse: Optional[float] = None   # RMSE of the transformation


class ThinPlateSpline:
    """
    Thin-Plate Spline interpolation for elastic deformation correction
    of scanned cadastral maps (Sajra).

    The TPS provides a smooth, non-rigid transformation that can correct
    for non-linear distortions in historical cloth maps (paper shrinkage,
    scanning artifacts, local datum distortions) that a rigid Helmert
    transformation cannot capture.

    Usage:
        tps = ThinPlateSpline(lambda_smooth=0.01)
        result = tps.fit(source_gcps, target_gcps)
        warped = tps.transform(source_points, result)
    """

    def __init__(self, lambda_smooth: float = 0.0, lambda_reg: Optional[float] = None):
        """
        Initialize TPS engine.
        """
        self.lambda_smooth = lambda_reg if lambda_reg is not None else lambda_smooth
        self._result: Optional[TPSResult] = None

    def fit(
        self,
        source_points: np.ndarray,
        target_points: np.ndarray,
        lambda_smooth: Optional[float] = None,
    ) -> TPSResult:
        lam = self.lambda_smooth if lambda_smooth is None else lambda_smooth
        self._result = self.fit_tps(source_points, target_points, lam)
        return self._result

    def transform(
        self,
        points: np.ndarray,
        result: Optional[TPSResult] = None,
    ) -> np.ndarray:
        res = result if result is not None else self._result
        if res is None:
            raise ValueError("TPS has not been fitted yet. Call fit() first.")
        return self.transform_points(points, res)

    @staticmethod
    def _tps_kernel(r: float) -> float:
        """
        TPS radial basis function: U(r) = r² · ln(r)

        This is the fundamental solution to the biharmonic equation
        in 2D, which minimizes bending energy.
        """
        if r < 1e-12:
            return 0.0
        return r * r * np.log(r)

    @staticmethod
    def _compute_kernel_matrix(points: np.ndarray) -> np.ndarray:
        """
        Compute the NxN kernel matrix K where K[i,j] = U(‖pᵢ - pⱼ‖).
        """
        n = len(points)
        K = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                r = np.linalg.norm(points[i] - points[j])
                val = ThinPlateSpline._tps_kernel(r)
                K[i, j] = val
                K[j, i] = val
        return K

    def fit(
        self,
        source_points: np.ndarray,
        target_points: np.ndarray,
    ) -> TPSResult:
        """
        Fit TPS transformation from source GCPs to target GCPs.

        Solves the TPS system:
        ┌ K + λI  P ┐ ┌ w ┐   ┌ v ┐
        │            │ │   │ = │   │
        └ Pᵀ     0  ┘ └ a ┘   └ 0 ┘

        where:
        - K: NxN kernel matrix
        - P: Nx3 polynomial matrix [1, x, y]
        - w: Nx2 TPS weights
        - a: 3x2 affine parameters
        - v: Nx2 target coordinates

        Parameters:
            source_points: Nx2 source (legacy map) GCP coordinates
            target_points: Nx2 target (drone ORI) GCP coordinates

        Returns:
            TPSResult with fitted parameters
        """
        n = len(source_points)
        if n < 3:
            raise ValueError("TPS requires at least 3 control points")

        # Build kernel matrix K (NxN)
        K = self._compute_kernel_matrix(source_points)

        # Build polynomial matrix P (Nx3): [1, x, y]
        P = np.hstack([np.ones((n, 1)), source_points])

        # Build the TPS system matrix
        # ┌ K + λI  P ┐
        # └ Pᵀ     0  ┘
        L = np.zeros((n + 3, n + 3))
        L[:n, :n] = K + self.lambda_smooth * np.eye(n)
        L[:n, n:n+3] = P
        L[n:n+3, :n] = P.T
        # Bottom-right 3x3 block remains zero

        # Build RHS: [target_points; zeros]
        rhs = np.zeros((n + 3, 2))
        rhs[:n] = target_points

        # Solve the system
        try:
            solution = np.linalg.solve(L, rhs)
        except np.linalg.LinAlgError:
            # Fall back to pseudo-inverse for ill-conditioned systems
            solution = np.linalg.lstsq(L, rhs, rcond=None)[0]

        weights = solution[:n]       # Nx2 TPS weights
        affine = solution[n:n+3]     # 3x2 affine parameters

        # Compute bending energy: E_bend = wᵀ K w
        bending_energy = float(np.trace(weights.T @ K @ weights))

        # Compute RMSE
        predicted = self.transform(source_points, TPSResult(
            affine_params=affine,
            weights=weights,
            control_points=source_points,
            bending_energy=bending_energy,
            lambda_smooth=self.lambda_smooth,
        ))
        residuals = target_points - predicted
        rmse = float(np.sqrt(np.mean(np.sum(residuals**2, axis=1))))

        self._result = TPSResult(
            affine_params=affine,
            weights=weights,
            control_points=source_points,
            bending_energy=bending_energy,
            lambda_smooth=self.lambda_smooth,
            rmse=rmse,
        )
        return self._result

    def transform(
        self,
        points: np.ndarray,
        result: Optional[TPSResult] = None,
    ) -> np.ndarray:
        """
        Apply fitted TPS transformation to new points.

        f(x) = a₁ + a₂x + a₃y + Σᵢ wᵢ U(‖x - cᵢ‖)

        Parameters:
            points: Mx2 array of points to transform
            result: Optional TPSResult from fit() (defaults to cached result)

        Returns:
            Mx2 array of transformed points
        """
        res = result if result is not None else self._result
        if res is None:
            raise ValueError("TPS has not been fitted yet. Call fit() first.")

        n_ctrl = len(res.control_points)
        m = len(points)

        # Compute kernel values between new points and control points
        U = np.zeros((m, n_ctrl))
        for i in range(m):
            for j in range(n_ctrl):
                r = np.linalg.norm(points[i] - res.control_points[j])
                U[i, j] = self._tps_kernel(r)

        # Polynomial part: [1, x, y]
        P = np.hstack([np.ones((m, 1)), points])

        # f(x) = P · affine + U · weights
        transformed = P @ res.affine_params + U @ res.weights

        return transformed

    def compute_jacobian(
        self,
        point: np.ndarray,
        result: TPSResult,
    ) -> np.ndarray:
        """
        Compute the Jacobian of the TPS transformation at a given point.
        Useful for propagating positional uncertainty through the warp.

        Returns:
            2x2 Jacobian matrix J = ∂f/∂x
        """
        eps = 1e-6
        J = np.zeros((2, 2))

        for dim in range(2):
            p_plus = point.copy()
            p_minus = point.copy()
            p_plus[dim] += eps
            p_minus[dim] -= eps

            f_plus = self.transform(p_plus.reshape(1, -1), result)[0]
            f_minus = self.transform(p_minus.reshape(1, -1), result)[0]

            J[:, dim] = (f_plus - f_minus) / (2 * eps)

        return J
