"""BhuSynch AI — CRS Transformation Utilities"""
from typing import Tuple
from pyproj import Transformer, CRS


# Pre-built transformers for common conversions
TRANSFORMERS = {}


def get_transformer(from_epsg: int, to_epsg: int) -> Transformer:
    """Get or create a cached CRS transformer."""
    key = (from_epsg, to_epsg)
    if key not in TRANSFORMERS:
        TRANSFORMERS[key] = Transformer.from_crs(
            CRS.from_epsg(from_epsg),
            CRS.from_epsg(to_epsg),
            always_xy=True,
        )
    return TRANSFORMERS[key]


def transform_7755_to_4326(x: float, y: float) -> Tuple[float, float]:
    """Transform from EPSG:7755 to EPSG:4326 (WGS84 lat/lon)."""
    t = get_transformer(7755, 4326)
    return t.transform(x, y)


def transform_4326_to_7755(lon: float, lat: float) -> Tuple[float, float]:
    """Transform from EPSG:4326 (WGS84) to EPSG:7755."""
    t = get_transformer(4326, 7755)
    return t.transform(lon, lat)
