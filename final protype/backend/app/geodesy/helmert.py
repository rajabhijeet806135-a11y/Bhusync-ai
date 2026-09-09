"""
BhuSynch AI — 7-Parameter Helmert Similarity Transformation
==============================================================
Subsystem 1: Automated Geodesy & Deep Feature Co-Registration

Implements the 7-parameter Helmert transformation for
GCP-based co-registration of legacy scanned maps to
modern drone orthoimagery.

Pipeline position: SuperPoint → LightGlue → RANSAC → [Helmert] → TPS → CORS
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class HelmertParameters:
    """
    Estimated 7-parameter Helmert transformation parameters.

    - tx, ty, tz: Translation parameters (meters)
    - rx, ry, rz: Rotation parameters (radians)
    - scale: Scale factor (unitless, close to 1.0)
    - rmse: Root Mean Square Error of residuals
    """
    tx: float = 0.0
    ty: float = 0.0
    tz: float = 0.0
    rx: float = 0.0
    ry: float = 0.0
    rz: float = 0.0
    scale: float = 1.0
    rmse: Optional[float] = None
    residuals: Optional[np.ndarray] = None


class HelmertTransformer:
    """7-parameter Bursa-Wolf Helmert Transformer."""

    def __init__(
        self,
        dx: float = 0.0,
        dy: float = 0.0,
        dz: float = 0.0,
        rx: float = 0.0,
        ry: float = 0.0,
        rz: float = 0.0,
        scale_ppm: float = 0.0,
    ):
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.rx = rx
        self.ry = ry
        self.rz = rz
        self.scale_ppm = scale_ppm
        self.scale = 1.0 + (scale_ppm * 1e-6)

    def transform(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        s = self.scale
        rx, ry, rz = self.rx, self.ry, self.rz
        xo = self.dx + s * (x - rz * y + ry * z)
        yo = self.dy + s * (rz * x + y - rx * z)
        zo = self.dz + s * (-ry * x + rx * y + z)
        return (xo, yo, zo)

    def inverse_transform(self, xo: float, yo: float, zo: float) -> Tuple[float, float, float]:
        inv_scale = 1.0 / self.scale
        x1 = (xo - self.dx) * inv_scale
        y1 = (yo - self.dy) * inv_scale
        z1 = (zo - self.dz) * inv_scale
        rx, ry, rz = self.rx, self.ry, self.rz
        x = x1 + rz * y1 - ry * z1
        y = -rz * x1 + y1 + rx * z1
        z = ry * x1 - rx * y1 + z1
        return (x, y, z)


class HelmertTransform:
    """
    7-Parameter Helmert Similarity Transformation.

    Given matched GCP pairs from SuperPoint+LightGlue, estimates
    the optimal 7 parameters (3 translations + 3 rotations + 1 scale)
    using least-squares minimization.

    For 2D map co-registration, a simplified 4-parameter version
    (2 translations + 1 rotation + 1 scale) is also available.
    """

    @staticmethod
    def estimate_2d(
        source_points: np.ndarray,
        target_points: np.ndarray,
    ) -> HelmertParameters:
        """
        Estimate 2D Helmert (4-parameter) transformation.

        Parameters:
            source_points: Nx2 array of source coordinates [x, y]
            target_points: Nx2 array of target coordinates [x, y]

        Returns:
            HelmertParameters with tx, ty, rz (rotation), scale, rmse
        """
        n = len(source_points)
        if n < 2:
            raise ValueError("At least 2 point pairs required for 2D Helmert")

        # Build design matrix for 4-parameter model
        # X_t = tx + scale * cos(θ) * X_s - scale * sin(θ) * Y_s
        # Y_t = ty + scale * sin(θ) * X_s + scale * cos(θ) * Y_s
        # Let a = scale * cos(θ), b = scale * sin(θ)
        # X_t = tx + a*X_s - b*Y_s
        # Y_t = ty + b*X_s + a*Y_s

        A = np.zeros((2 * n, 4))
        L = np.zeros(2 * n)

        for i in range(n):
            xs, ys = source_points[i]
            xt, yt = target_points[i]
            # X equation
            A[2 * i] = [1, 0, xs, -ys]
            L[2 * i] = xt
            # Y equation
            A[2 * i + 1] = [0, 1, ys, xs]
            L[2 * i + 1] = yt

        # Least squares: x = (A^T A)^{-1} A^T L
        ATA = A.T @ A
        ATL = A.T @ L
        params = np.linalg.solve(ATA, ATL)

        tx, ty, a, b = params
        scale = np.sqrt(a**2 + b**2)
        rotation = np.arctan2(b, a)

        # Compute residuals
        L_pred = A @ params
        v = L - L_pred
        rmse = np.sqrt(np.sum(v**2) / (2 * n - 4))

        return HelmertParameters(
            tx=tx, ty=ty, tz=0.0,
            rx=0.0, ry=0.0, rz=rotation,
            scale=scale,
            rmse=rmse,
            residuals=v.reshape(n, 2),
        )

    @staticmethod
    def estimate_3d(
        source_points: np.ndarray,
        target_points: np.ndarray,
    ) -> HelmertParameters:
        """
        Estimate 3D Helmert (7-parameter) transformation using
        linearized least-squares.

        Parameters:
            source_points: Nx3 array of source ECEF coordinates [X, Y, Z]
            target_points: Nx3 array of target ECEF coordinates [X, Y, Z]

        Returns:
            HelmertParameters with all 7 parameters and RMSE
        """
        n = len(source_points)
        if n < 3:
            raise ValueError("At least 3 point pairs required for 3D Helmert")

        # Build design matrix for 7-parameter model
        # X_t = ΔX + (1+s) * (X_s - Rz*Y_s + Ry*Z_s)
        # Y_t = ΔY + (1+s) * (Rz*X_s + Y_s - Rx*Z_s)
        # Z_t = ΔZ + (1+s) * (-Ry*X_s + Rx*Y_s + Z_s)
        # Linearized: 7 unknowns [ΔX, ΔY, ΔZ, Rx, Ry, Rz, s]

        A = np.zeros((3 * n, 7))
        L = np.zeros(3 * n)

        for i in range(n):
            xs, ys, zs = source_points[i]
            xt, yt, zt = target_points[i]

            # X equation
            A[3 * i] = [1, 0, 0, 0, zs, -ys, xs]
            L[3 * i] = xt - xs

            # Y equation
            A[3 * i + 1] = [0, 1, 0, -zs, 0, xs, ys]
            L[3 * i + 1] = yt - ys

            # Z equation
            A[3 * i + 2] = [0, 0, 1, ys, -xs, 0, zs]
            L[3 * i + 2] = zt - zs

        # Least squares: x = (A^T A)^{-1} A^T L
        ATA = A.T @ A
        ATL = A.T @ L
        params = np.linalg.solve(ATA, ATL)

        dx, dy, dz, rx, ry, rz, s = params

        # Compute residuals
        L_pred = A @ params
        v = L - L_pred
        rmse = np.sqrt(np.sum(v**2) / (3 * n - 7))

        return HelmertParameters(
            tx=dx, ty=dy, tz=dz,
            rx=rx, ry=ry, rz=rz,
            scale=1.0 + s,
            rmse=rmse,
            residuals=v.reshape(n, 3),
        )

    @staticmethod
    def apply_2d(
        params: HelmertParameters,
        points: np.ndarray,
    ) -> np.ndarray:
        """
        Apply 2D Helmert transformation to a set of points.

        Parameters:
            params: Estimated HelmertParameters
            points: Nx2 array of source coordinates

        Returns:
            Nx2 array of transformed coordinates
        """
        a = params.scale * np.cos(params.rz)
        b = params.scale * np.sin(params.rz)

        transformed = np.zeros_like(points)
        for i in range(len(points)):
            x, y = points[i]
            transformed[i, 0] = params.tx + a * x - b * y
            transformed[i, 1] = params.ty + b * x + a * y

        return transformed

    @staticmethod
    def apply_3d(
        params: HelmertParameters,
        points: np.ndarray,
    ) -> np.ndarray:
        """
        Apply 3D Helmert transformation to ECEF coordinates.

        Section 2.1 formula:
        [X,Y,Z]_t = [ΔX,ΔY,ΔZ] + (1+s) · R · [X,Y,Z]_s

        Parameters:
            params: Estimated HelmertParameters
            points: Nx3 array of source ECEF coordinates

        Returns:
            Nx3 array of transformed ECEF coordinates
        """
        T = np.array([params.tx, params.ty, params.tz])
        R = np.array([
            [1.0,       -params.rz,  params.ry],
            [params.rz,  1.0,       -params.rx],
            [-params.ry, params.rx,  1.0],
        ])

        transformed = np.zeros_like(points)
        for i in range(len(points)):
            transformed[i] = T + params.scale * (R @ points[i])

        return transformed

