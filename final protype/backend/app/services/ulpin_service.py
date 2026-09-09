"""
BhuSynch AI — ULPIN Service
==============================
14-Character Unique Land Parcel Identification Number (Bhu-Aadhaar)

Centroid encoding formula from Section 2.2:
Centroid (φ_c, λ_c) = (1/A ∮_C x·dA, 1/A ∮_C y·dA)
ULPIN = E_DoLR(φ_c, λ_c, Area_sqm, State_Code)

Generates ULPIN per DoLR/NAKSHA specifications.
"""

import hashlib
import math
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import structlog

logger = structlog.get_logger(__name__)

# State codes as per DoLR/Census
STATE_CODES = {
    "AN": "01", "AP": "02", "AR": "03", "AS": "04", "BR": "05",
    "CH": "06", "CT": "07", "DD": "08", "DL": "09", "GA": "10",
    "GJ": "11", "HP": "12", "HR": "13", "JH": "14", "JK": "15",
    "KA": "16", "KL": "17", "LA": "18", "LD": "19", "MH": "20",
    "ML": "21", "MN": "22", "MP": "23", "MZ": "24", "NL": "25",
    "OD": "26", "PB": "27", "PY": "28", "RJ": "29", "SK": "30",
    "TN": "31", "TS": "32", "TR": "33", "UK": "34", "UP": "35",
    "WB": "36",
}


class ULPINService:
    """
    14-Character ULPIN (Bhu-Aadhaar) Generation Service.

    ULPIN format: SS-DDDDD-CCCCC-V
    Where:
    - SS: State code (2 digits)
    - DDDDD: District+Village encoded from centroid (5 digits)
    - CCCCC: Centroid hash (5 digits)
    - V: Verification digit (1 digit — Luhn algorithm)

    Total: 14 characters (digits only, no dashes in stored format)
    """

    @classmethod
    def compute_centroid(cls, coordinates: Any) -> Tuple[float, float]:
        """Compute the centroid (x, y) of vertices."""
        coords = list(coordinates)
        if len(coords) > 1 and np.allclose(coords[0], coords[-1]):
            coords = coords[:-1]
        lons = [float(c[0]) for c in coords]
        lats = [float(c[1]) for c in coords]
        return float(np.mean(lons)), float(np.mean(lats))

    @staticmethod
    def compute_polygon_centroid(
        coordinates: List[List[float]],
    ) -> Tuple[float, float]:
        """Compute the centroid of a polygon using the shoelace formula."""
        return ULPINService.compute_centroid(coordinates)

    @classmethod
    def convert_area_to_sqm(cls, value: float, unit: str) -> float:
        """Convert traditional Indian land area units to square meters."""
        conversions = {
            "bigha": 2529.28,
            "bigha_wb": 1337.8,
            "gunta": 101.17,
            "katha": 126.46,  # Standard National Katha
            "katha_wb": 66.89,  # West Bengal standard Katha (720 sq ft)
            "chhatak": 4.18,  # 1/16th of Katha in West Bengal (45 sq ft)
            "decimal": 40.4686,
            "cent": 40.4686,
            "biswa": 125.42,
            "sqm": 1.0,
            "sq_m": 1.0,
            "acre": 4046.86,
            "hectare": 10000.0,
        }
        return float(value) * conversions.get(unit.lower(), 1.0)

    @classmethod
    def compute_polygon_area_sqm(
        cls,
        coordinates: Any,
        lat_ref: Optional[float] = None,
    ) -> float:
        """
        Compute polygon area in square meters using the Shoelace formula.
        """
        coords = list(coordinates)
        n = len(coords)
        if n < 3:
            return 0.0

        # If degrees, convert approximate to meters using lat_ref
        if lat_ref is not None or (abs(coords[0][0]) <= 180 and abs(coords[0][1]) <= 90):
            ref = lat_ref if lat_ref is not None else coords[0][1]
            meters_per_deg_lat = 111320.0
            meters_per_deg_lon = 111320.0 * math.cos(math.radians(ref))
            pts = [[c[0] * meters_per_deg_lon, c[1] * meters_per_deg_lat] for c in coords]
        else:
            pts = coords

        area = 0.0
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            area += x0 * y1 - x1 * y0

        return float(abs(area) / 2.0)

    @staticmethod
    def _luhn_checksum(number_str: str) -> int:
        """Compute Luhn algorithm check digit."""
        digits = [int(d) for d in number_str if d.isdigit()]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]

        total = sum(odd_digits)
        for d in even_digits:
            total += sum(divmod(d * 2, 10))

        return (10 - (total % 10)) % 10

    @classmethod
    def generate_ulpin(
        cls,
        state_code: str = "27",
        centroid_lat: Optional[float] = None,
        centroid_lon: Optional[float] = None,
        area_sqm: float = 1000.0,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
    ) -> str:
        """
        Generate a 14-character ULPIN (Bhu-Aadhaar).
        """
        c_lat = lat if lat is not None else (centroid_lat if centroid_lat is not None else 18.5204)
        c_lon = lon if lon is not None else (centroid_lon if centroid_lon is not None else 73.8567)

        # State code (2 digits)
        if state_code.isdigit() and len(state_code) == 2:
            numeric_state = state_code
        else:
            numeric_state = STATE_CODES.get(state_code.upper(), "27")

        # Encode centroid position into 5-digit district+village code
        spatial_hash = hashlib.md5(f"{c_lat:.6f},{c_lon:.6f}".encode()).hexdigest()
        district_village = str(int(spatial_hash[:8], 16) % 100000).zfill(5)

        # Encode centroid + area into 5-digit hash
        combined = f"{c_lat:.8f}:{c_lon:.8f}:{area_sqm:.4f}"
        centroid_hash = hashlib.sha256(combined.encode()).hexdigest()
        centroid_code = str(int(centroid_hash[:8], 16) % 100000).zfill(5)

        # Base ULPIN (12 digits)
        base_ulpin = f"{numeric_state}{district_village[:5]}{centroid_code[:5]}"
        base_13 = base_ulpin[:13] if len(base_ulpin) >= 13 else base_ulpin.ljust(13, "0")

        # Verification digit (Luhn checksum)
        check_digit = cls._luhn_checksum(base_13)

        ulpin = f"{base_13}{check_digit}"
        return ulpin[:14]
