"""
BhuSynch AI — CORS Constrained Least-Squares Adjustment
=========================================================
Subsystem 1, Step 4: Survey of India CORS Network Adjustment

Exact formula from Section 2.1:

    x̂ = (AᵀPA)⁻¹ AᵀPL

    RMSE = √(Σ vᵢ² / (n - m))

where:
    A = Design matrix (partial derivatives of observation equations)
    P = Weight matrix (inverse of observation covariance)
    L = Observation vector (discrepancies)
    v = Residual vector (v = A·x̂ - L)
    n = Number of observations
    m = Number of unknowns

Pipeline position: SuperPoint → LightGlue → RANSAC → Helmert → TPS → [CORS]
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class CORSStation:
    """
    Survey of India CORS (Continuously Operating Reference Station) record.
    """
    station_id: str
    latitude_deg: float
    longitude_deg: float
    height_m: float
    x_ecef: float
    y_ecef: float
    z_ecef: float
    sigma_x: float  # Standard deviation in X (meters)
    sigma_y: float  # Standard deviation in Y (meters)
    sigma_z: float  # Standard deviation in Z (meters)


@dataclass
class AdjustmentResult:
    """Result of the least-squares adjustment."""
    adjusted_params: np.ndarray     # Estimated parameter vector x̂
    residuals: np.ndarray           # Residual vector v
    rmse: float                     # Root Mean Square Error
    covariance_matrix: np.ndarray   # Parameter covariance matrix Σ
    a_posteriori_sigma: float       # A-posteriori unit weight variance
    dof: int                        # Degrees of freedom (n - m)
    chi_squared: float              # Chi-squared statistic
    redundancy_numbers: np.ndarray  # Per-observation redundancy numbers

    def __iter__(self):
        yield self.adjusted_params
        yield self.rmse
        yield self.residuals


class CORSAdjustment:
    """
    CORS Constrained Least-Squares Adjustment Engine.

    Performs weighted least-squares adjustment of GCP coordinates
    constrained by Survey of India CORS station positions.

    The adjustment simultaneously estimates:
    1. Transformation parameters (datum shift corrections)
    2. Adjusted GCP coordinates
    3. Per-vertex error covariance ellipses

    Usage:
        adj = CORSAdjustment()
        result = adj.adjust(
            design_matrix=A,
            weight_matrix=P,
            observation_vector=L,
        )
    """

    @staticmethod
    def build_weight_matrix(
        sigmas: np.ndarray,
        correlation_matrix: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Build the weight matrix P from observation standard deviations.

        P = Σ_obs⁻¹ where Σ_obs is the observation covariance matrix.

        For uncorrelated observations: P = diag(1/σ²)
        For correlated observations: P = (D · C · D)⁻¹
        where D = diag(σ) and C = correlation matrix.

        Parameters:
            sigmas: Array of standard deviations for each observation
            correlation_matrix: Optional NxN correlation matrix

        Returns:
            NxN weight matrix
        """
        n = len(sigmas)

        if correlation_matrix is None:
            # Uncorrelated observations: diagonal weight matrix
            return np.diag(1.0 / (sigmas ** 2))
        else:
            # Correlated observations: full covariance matrix
            D = np.diag(sigmas)
            cov = D @ correlation_matrix @ D
            return np.linalg.inv(cov)

    @staticmethod
    def adjust(
        design_matrix: np.ndarray,
        weight_matrix: np.ndarray,
        observation_vector: np.ndarray,
        constraints: Optional[Tuple[np.ndarray, np.ndarray]] = None,
    ) -> AdjustmentResult:
        """
        Perform weighted least-squares adjustment.

        Section 2.1 formula:
            x̂ = (AᵀPA)⁻¹ AᵀPL
            RMSE = √(Σ vᵢ² / (n - m))

        Parameters:
            design_matrix: A — nxm design matrix
            weight_matrix: P — nxn weight matrix
            observation_vector: L — n-vector of observations
            constraints: Optional (C, d) where Cx̂ = d for CORS constraints

        Returns:
            AdjustmentResult with adjusted parameters, residuals, RMSE
        """
        A = np.array(design_matrix, dtype=np.float64)
        arg1 = np.array(weight_matrix, dtype=np.float64)
        arg2 = np.array(observation_vector, dtype=np.float64)
        if arg1.ndim == 1 and arg2.ndim == 2:
            L, P = arg1, arg2
        else:
            P, L = arg1, arg2
        n, m = A.shape

        if constraints is not None:
            # Constrained least-squares using Lagrange multipliers
            C, d = constraints
            c = C.shape[0]

            # Build the augmented normal equation system
            # ┌ AᵀPA  Cᵀ ┐ ┌ x̂ ┐   ┌ AᵀPL ┐
            # └  C     0  ┘ └ λ  ┘ = └  d    ┘
            N = A.T @ P @ A
            n_vec = A.T @ P @ L

            aug_matrix = np.zeros((m + c, m + c))
            aug_matrix[:m, :m] = N
            aug_matrix[:m, m:m+c] = C.T
            aug_matrix[m:m+c, :m] = C

            aug_rhs = np.zeros(m + c)
            aug_rhs[:m] = n_vec
            aug_rhs[m:m+c] = d

            aug_solution = np.linalg.solve(aug_matrix, aug_rhs)
            x_hat = aug_solution[:m]
        else:
            # Standard weighted least-squares
            # Normal equation: (AᵀPA) x̂ = AᵀPL
            N = A.T @ P @ A  # Normal equation matrix
            n_vec = A.T @ P @ L  # Normal equation RHS

            x_hat = np.linalg.solve(N, n_vec)

        # Compute residuals: v = A·x̂ - L
        v = A @ x_hat - L

        # Degrees of freedom
        dof = n - m

        # A-posteriori unit weight variance
        vPv = float(v.T @ P @ v)
        sigma0_sq = vPv / dof if dof > 0 else 0.0

        # RMSE = √(Σ vᵢ² / (n - m))
        rmse = float(np.sqrt(np.sum(v ** 2) / dof)) if dof > 0 else 0.0

        # Parameter covariance matrix: Σ_x̂ = σ₀² (AᵀPA)⁻¹
        N_inv = np.linalg.inv(A.T @ P @ A)
        covariance = sigma0_sq * N_inv

        # Chi-squared statistic for goodness of fit
        chi_squared = vPv

        # Redundancy numbers (hat matrix diagonal)
        H = A @ N_inv @ A.T @ P
        redundancy_numbers = 1.0 - np.diag(H)

        return AdjustmentResult(
            adjusted_params=x_hat,
            residuals=v,
            rmse=rmse,
            covariance_matrix=covariance,
            a_posteriori_sigma=float(np.sqrt(sigma0_sq)),
            dof=dof,
            chi_squared=chi_squared,
            redundancy_numbers=redundancy_numbers,
        )

    @staticmethod
    def compute_error_ellipse(
        covariance_2x2: np.ndarray,
        confidence: float = 0.95,
    ) -> Tuple[float, float, float]:
        """
        Compute error ellipse parameters from a 2x2 covariance matrix.

        Used for generating vertex covariance error ellipses (Subsystem 4):
        Σ = (Σ wₛ Aₛᵀ Aₛ)⁻¹

        Parameters:
            covariance_2x2: 2x2 position covariance matrix
            confidence: Confidence level (default 95%)

        Returns:
            (semi_major_m, semi_minor_m, orientation_deg)
        """
        from scipy.stats import chi2

        eigenvalues, eigenvectors = np.linalg.eigh(covariance_2x2)

        # Sort by descending eigenvalue
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Chi-squared critical value for 2 DoF at given confidence
        k = chi2.ppf(confidence, df=2)

        # Semi-axes in meters
        semi_major = float(np.sqrt(k * eigenvalues[0]))
        semi_minor = float(np.sqrt(k * eigenvalues[1]))

        # Orientation of major axis (degrees from East, counter-clockwise)
        orientation = float(np.degrees(np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0])))

        return semi_major, semi_minor, orientation

    @staticmethod
    def merge_multi_source_covariance(
        covariances: List[np.ndarray],
        weights: List[float],
    ) -> np.ndarray:
        """
        Merge covariance matrices from multiple data sources
        using weighted combination.

        Subsystem 4 formula: Σ = (Σ wₛ Aₛᵀ Aₛ)⁻¹

        Parameters:
            covariances: List of 2x2 covariance matrices per source
            weights: Source reliability weights

        Returns:
            Merged 2x2 covariance matrix
        """
        accumulated = np.zeros((2, 2))
        for cov, w in zip(covariances, weights):
            # Invert each covariance to get precision, then weight
            precision = np.linalg.inv(cov)
            accumulated += w * precision

        # Final covariance is the inverse of accumulated precision
        merged_covariance = np.linalg.inv(accumulated)
        return merged_covariance


CORSLeastSquaresAdjuster = CORSAdjustment

