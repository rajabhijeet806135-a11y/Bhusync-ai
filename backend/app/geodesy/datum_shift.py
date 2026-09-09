"""
BhuSynch AI — Datum Shift Engine
==================================
Subsystem 1, Step 1: Kalianpur 1830 → WGS84 / EPSG:7755

Implements the 7-parameter Bursa-Wolf (Helmert) datum transformation
as specified in Section 2.1:

    ┌ X_WGS84 ┐     ┌ ΔX ┐                    ┌  1   -Rz   Ry ┐ ┌ X_Everest ┐
    │ Y_WGS84 │  =  │ ΔY │ + (1 + s × 10⁻⁶)  │  Rz   1   -Rx │ │ Y_Everest │
    └ Z_WGS84 ┘     └ ΔZ ┘                    └ -Ry   Rx   1  ┘ └ Z_Everest ┘

Reference datum parameters for Kalianpur 1830 (Everest 1830) to WGS84
are sourced from Survey of India CORS network.
"""

import math
from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np


@dataclass
class DatumParameters:
    """
    Bursa-Wolf 7-parameter transformation parameters.
    Translation in meters, rotation in arc-seconds, scale in ppm.
    """
    delta_x: float  # Translation X (meters)
    delta_y: float  # Translation Y (meters)
    delta_z: float  # Translation Z (meters)
    rx: float       # Rotation about X (arc-seconds)
    ry: float       # Rotation about Y (arc-seconds)
    rz: float       # Rotation about Z (arc-seconds)
    scale: float    # Scale factor (ppm)


# ── Pre-defined Datum Parameters ─────────────────────────────────────
# Kalianpur 1830 (Everest 1830) → WGS84
# Source: Survey of India / EPSG Registry
KALIANPUR_TO_WGS84 = DatumParameters(
    delta_x=295.0,
    delta_y=736.0,
    delta_z=257.0,
    rx=0.0,
    ry=0.0,
    rz=0.0,
    scale=0.0,
)

# Everest 1830 ellipsoid parameters
EVEREST_1830 = {
    "a": 6377276.345,  # Semi-major axis (m)
    "b": 6356075.4133,  # Semi-minor axis (m)
    "f": 1 / 300.8017,  # Flattening
}

# WGS84 ellipsoid parameters
WGS84 = {
    "a": 6378137.0,      # Semi-major axis (m)
    "b": 6356752.3142,   # Semi-minor axis (m)
    "f": 1 / 298.257223563,  # Flattening
}


class DatumShiftEngine:
    """
    Performs datum transformation between Kalianpur 1830 (Everest)
    and WGS84 coordinate systems using the Bursa-Wolf model.

    Usage:
        engine = DatumShiftEngine()
        lat_wgs84, lon_wgs84, h_wgs84 = engine.kalianpur_to_wgs84(lat, lon, height)
    """

    def __init__(
        self,
        params: DatumParameters = KALIANPUR_TO_WGS84,
        source_ellipsoid: dict = None,
        target_ellipsoid: dict = None,
    ):
        self.params = params
        self.source = source_ellipsoid or EVEREST_1830
        self.target = target_ellipsoid or WGS84

    def geodetic_to_cartesian(self, lat_deg: float, lon_deg: float, h: float = 0.0) -> Tuple[float, float, float]:
        """Convert geodetic (lat, lon, h) to cartesian (X, Y, Z) in meters."""
        return self._geodetic_to_ecef(lat_deg, lon_deg, h, self.source["a"], self.source["f"])

    def cartesian_to_geodetic(self, X: float, Y: float, Z: float, ellipsoid: Optional[dict] = None) -> Tuple[float, float, float]:
        """Convert cartesian (X, Y, Z) to geodetic (lat, lon, h)."""
        ell = ellipsoid or self.source
        return self._ecef_to_geodetic(X, Y, Z, ell["a"], ell["f"])

    def shift_kalianpur_to_wgs84(self, lat_deg: float, lon_deg: float, h: float = 0.0) -> Tuple[float, float]:
        """Convert Kalianpur 1830 lat/lon to WGS84 lat/lon."""
        lat_wgs, lon_wgs, _ = self.kalianpur_to_wgs84(lat_deg, lon_deg, h)
        return lat_wgs, lon_wgs

    @staticmethod
    def _arcsec_to_rad(arcsec: float) -> float:
        """Convert arc-seconds to radians."""
        return arcsec * math.pi / (180.0 * 3600.0)

    @staticmethod
    def _geodetic_to_ecef(
        lat_deg: float, lon_deg: float, h: float, a: float, f: float
    ) -> Tuple[float, float, float]:
        """
        Convert geodetic coordinates (lat, lon, height) to ECEF (X, Y, Z).

        Parameters:
            lat_deg: Latitude in degrees
            lon_deg: Longitude in degrees
            h: Ellipsoidal height in meters
            a: Semi-major axis of the ellipsoid
            f: Flattening of the ellipsoid

        Returns:
            (X, Y, Z) in meters
        """
        lat = math.radians(lat_deg)
        lon = math.radians(lon_deg)
        e2 = 2 * f - f * f  # Eccentricity squared
        N = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)  # Radius of curvature

        X = (N + h) * math.cos(lat) * math.cos(lon)
        Y = (N + h) * math.cos(lat) * math.sin(lon)
        Z = (N * (1 - e2) + h) * math.sin(lat)

        return X, Y, Z

    @staticmethod
    def _ecef_to_geodetic(
        X: float, Y: float, Z: float, a: float, f: float,
        max_iter: int = 20, tol: float = 1e-12,
    ) -> Tuple[float, float, float]:
        """
        Convert ECEF (X, Y, Z) back to geodetic (lat, lon, height).
        Uses Bowring's iterative method.

        Returns:
            (latitude_deg, longitude_deg, height_m)
        """
        e2 = 2 * f - f * f
        b = a * (1 - f)
        ep2 = (a * a - b * b) / (b * b)
        p = math.sqrt(X * X + Y * Y)
        lon = math.atan2(Y, X)

        # Initial approximation using Bowring
        theta = math.atan2(Z * a, p * b)
        lat = math.atan2(
            Z + ep2 * b * math.sin(theta) ** 3,
            p - e2 * a * math.cos(theta) ** 3,
        )

        for _ in range(max_iter):
            N = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
            lat_new = math.atan2(Z + e2 * N * math.sin(lat), p)
            if abs(lat_new - lat) < tol:
                lat = lat_new
                break
            lat = lat_new

        N = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
        h = p / math.cos(lat) - N if abs(math.cos(lat)) > 1e-10 else Z / math.sin(lat) - N * (1 - e2)

        return math.degrees(lat), math.degrees(lon), h

    def _build_rotation_matrix(self) -> np.ndarray:
        """
        Build the Bursa-Wolf rotation matrix from the 7 parameters.

        Section 2.1 formula:
        R = ┌  1   -Rz   Ry ┐
            │  Rz   1   -Rx │
            └ -Ry   Rx   1  ┘

        Rotation angles are converted from arc-seconds to radians.
        """
        rx = self._arcsec_to_rad(self.params.rx)
        ry = self._arcsec_to_rad(self.params.ry)
        rz = self._arcsec_to_rad(self.params.rz)

        R = np.array([
            [1.0,  -rz,  ry],
            [rz,   1.0, -rx],
            [-ry,  rx,  1.0],
        ])
        return R

    def transform_ecef(
        self, X_src: float, Y_src: float, Z_src: float
    ) -> Tuple[float, float, float]:
        """
        Apply the 7-parameter Bursa-Wolf transformation in ECEF space.

        Formula (Section 2.1):
        [X,Y,Z]_target = [ΔX,ΔY,ΔZ] + (1 + s × 10⁻⁶) · R · [X,Y,Z]_source
        """
        T = np.array([self.params.delta_x, self.params.delta_y, self.params.delta_z])
        R = self._build_rotation_matrix()
        s = 1.0 + self.params.scale * 1e-6
        src = np.array([X_src, Y_src, Z_src])

        target = T + s * (R @ src)
        return float(target[0]), float(target[1]), float(target[2])

    def kalianpur_to_wgs84(
        self, lat_deg: float, lon_deg: float, height_m: float = 0.0
    ) -> Tuple[float, float, float]:
        """
        Transform coordinates from Kalianpur 1830 (Everest) to WGS84.

        Pipeline: Geodetic → ECEF → Bursa-Wolf → ECEF → Geodetic

        Parameters:
            lat_deg: Latitude in degrees (Everest datum)
            lon_deg: Longitude in degrees (Everest datum)
            height_m: Ellipsoidal height in meters

        Returns:
            (lat_wgs84, lon_wgs84, height_wgs84)
        """
        # Step 1: Geodetic → ECEF (on Everest ellipsoid)
        X_ev, Y_ev, Z_ev = self._geodetic_to_ecef(
            lat_deg, lon_deg, height_m,
            self.source["a"], self.source["f"]
        )

        # Step 2: Apply Bursa-Wolf 7-parameter transformation
        X_wgs, Y_wgs, Z_wgs = self.transform_ecef(X_ev, Y_ev, Z_ev)

        # Step 3: ECEF → Geodetic (on WGS84 ellipsoid)
        lat_wgs, lon_wgs, h_wgs = self._ecef_to_geodetic(
            X_wgs, Y_wgs, Z_wgs,
            self.target["a"], self.target["f"]
        )

        return lat_wgs, lon_wgs, h_wgs

    def transform_batch(
        self, coordinates: np.ndarray
    ) -> np.ndarray:
        """
        Transform a batch of [lat, lon, height] coordinates.

        Parameters:
            coordinates: Nx3 array of [lat_deg, lon_deg, height_m]

        Returns:
            Nx3 array of transformed [lat_deg, lon_deg, height_m]
        """
        results = np.zeros_like(coordinates)
        for i in range(len(coordinates)):
            results[i] = self.kalianpur_to_wgs84(*coordinates[i])
        return results
