"""
BhuSynch AI — Fréchet Elastic Graph Optimization
===================================================
Subsystem 3: GeoAI Edge Conflation

Exact formula from Section 2.3:

min_d Σ_{i∈V_L} D_Fréchet(E_{L,i}, E_{P,match})
    + γ Σ_{(i,j)∈E_L} ‖(p_i + d_i - p_j - d_j) - (p_i - p_j)‖²

First term: Fréchet distance between legacy edges and SAM-Geo edges
Second term: Topology preservation (edge length/direction consistency)
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class FrechetMatchResult:
    """Result of Fréchet matching between two polylines."""
    distance: float
    coupling: List[Tuple[int, int]]  # Optimal coupling indices
    max_leash_length: float


class FrechetMatcher:
    """
    Deformable Vector Conflation using Fréchet Distance.

    Matches legacy khasra polygon edges to SAM-Geo extracted boundaries
    using the discrete Fréchet distance as the matching criterion,
    then optimizes vertex displacements to minimize the combined
    Fréchet + topology preservation objective.
    """

    def frechet_distance(self, P: np.ndarray, Q: np.ndarray) -> float:
        return self.discrete_frechet_distance(P, Q)

    def match_edges(self, legacy: np.ndarray, detected: np.ndarray) -> List[Tuple[int, int]]:
        res = self.frechet_distance_dp(legacy, detected)
        return res.coupling

    @staticmethod
    def discrete_frechet_distance(P: np.ndarray, Q: np.ndarray) -> float:
        """
        Compute the discrete Fréchet distance between two polylines.

        Parameters:
            P: Nx2 array — first polyline vertices
            Q: Mx2 array — second polyline vertices

        Returns:
            Discrete Fréchet distance
        """
        n = len(P)
        m = len(Q)
        dp = np.full((n, m), -1.0)

        def _dist(i: int, j: int) -> float:
            return float(np.linalg.norm(P[i] - Q[j]))

        def _recurse(i: int, j: int) -> float:
            if dp[i, j] > -0.5:
                return dp[i, j]
            d = _dist(i, j)
            if i == 0 and j == 0:
                dp[i, j] = d
            elif i > 0 and j == 0:
                dp[i, j] = max(_recurse(i - 1, 0), d)
            elif i == 0 and j > 0:
                dp[i, j] = max(_recurse(0, j - 1), d)
            else:
                dp[i, j] = max(
                    min(
                        _recurse(i - 1, j),
                        _recurse(i - 1, j - 1),
                        _recurse(i, j - 1),
                    ),
                    d,
                )
            return dp[i, j]

        return _recurse(n - 1, m - 1)

    @staticmethod
    def frechet_distance_dp(P: np.ndarray, Q: np.ndarray) -> FrechetMatchResult:
        """
        Compute discrete Fréchet distance with optimal coupling.
        Non-recursive DP implementation for large polylines.
        """
        n, m = len(P), len(Q)
        dp = np.full((n, m), np.inf)

        # Base cases
        dp[0, 0] = np.linalg.norm(P[0] - Q[0])

        for i in range(1, n):
            dp[i, 0] = max(dp[i-1, 0], np.linalg.norm(P[i] - Q[0]))
        for j in range(1, m):
            dp[0, j] = max(dp[0, j-1], np.linalg.norm(P[0] - Q[j]))

        for i in range(1, n):
            for j in range(1, m):
                d = np.linalg.norm(P[i] - Q[j])
                dp[i, j] = max(d, min(dp[i-1, j], dp[i-1, j-1], dp[i, j-1]))

        # Backtrack for coupling
        coupling = []
        i, j = n - 1, m - 1
        coupling.append((i, j))
        while i > 0 or j > 0:
            if i == 0:
                j -= 1
            elif j == 0:
                i -= 1
            else:
                candidates = [
                    (dp[i-1, j-1], i-1, j-1),
                    (dp[i-1, j], i-1, j),
                    (dp[i, j-1], i, j-1),
                ]
                _, best_i, best_j = min(candidates, key=lambda x: x[0])
                i, j = best_i, best_j
            coupling.append((i, j))
        coupling.reverse()

        return FrechetMatchResult(
            distance=float(dp[n-1, m-1]),
            coupling=coupling,
            max_leash_length=float(dp[n-1, m-1]),
        )

    @staticmethod
    def optimize_displacements(
        legacy_vertices: np.ndarray,
        target_vertices: np.ndarray,
        edges: List[Tuple[int, int]],
        gamma: float = 0.5,
        max_iterations: int = 100,
        tolerance: float = 1e-4,
    ) -> np.ndarray:
        """
        Optimize vertex displacements for deformable conflation.

        Section 2.3 formula:
        min_d Σ D_Fréchet(E_L, E_P) + γ Σ ‖(p_i+d_i-p_j-d_j)-(p_i-p_j)‖²

        Uses gradient descent to minimize the combined objective.

        Parameters:
            legacy_vertices: Nx2 legacy polygon vertices
            target_vertices: Nx2 matched target positions
            edges: Edge connectivity (i, j) pairs
            gamma: Topology preservation weight
            max_iterations: Maximum optimization iterations
            tolerance: Convergence tolerance

        Returns:
            Nx2 optimal displacement vectors
        """
        n = len(legacy_vertices)
        d = np.zeros((n, 2))  # Displacement vectors
        learning_rate = 0.01

        for iteration in range(max_iterations):
            grad = np.zeros((n, 2))

            # Data fidelity gradient: ∂/∂d_i [‖(p_i + d_i) - t_i‖²]
            for i in range(n):
                residual = (legacy_vertices[i] + d[i]) - target_vertices[i]
                grad[i] += 2.0 * residual

            # Topology preservation gradient
            for (i, j) in edges:
                original_edge = legacy_vertices[i] - legacy_vertices[j]
                displaced_edge = (legacy_vertices[i] + d[i]) - (legacy_vertices[j] + d[j])
                diff = displaced_edge - original_edge
                grad[i] += 2.0 * gamma * diff
                grad[j] -= 2.0 * gamma * diff

            # Update
            d -= learning_rate * grad

            # Check convergence
            grad_norm = np.linalg.norm(grad)
            if grad_norm < tolerance:
                break

        return d
