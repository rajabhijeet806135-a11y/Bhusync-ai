"""
BhuSynch AI — Universal Geometry & CRS Utilities
==================================================
Converts PostGIS EWKB, GeoAlchemy2 elements, Shapely geometries, and GeoJSON dicts.
Handles coordinate reprojection between EPSG:7755 (SOI LCC), EPSG:4326 (WGS84), and EPSG:3857.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import json
import re

import shapely
from shapely import wkb, wkt
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer, CRS

try:
    from geoalchemy2.elements import WKBElement, WKTElement
except ImportError:
    WKBElement, WKTElement = None, None


# Cache for pyproj Transformers
_TRANSFORMER_CACHE: Dict[Tuple[int, int], Transformer] = {}


def parse_crs(crs_input: Optional[Union[int, str]]) -> int:
    """
    Parse a CRS string, URI, or integer into an EPSG integer code.
    Examples:
        'EPSG:7755' -> 7755
        'http://www.opengis.net/def/crs/EPSG/0/4326' -> 4326
        '4326' -> 4326
        None -> 4326 (default GeoJSON standard)
    """
    if crs_input is None:
        return 4326
    if isinstance(crs_input, int):
        return crs_input

    crs_str = str(crs_input).strip()
    # Check for URI pattern
    match = re.search(r"EPSG(?:/0/|:)(\d+)", crs_str, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Check for direct integer string
    if crs_str.isdigit():
        return int(crs_str)

    return 4326


def get_transformer(from_epsg: int, to_epsg: int) -> Optional[Transformer]:
    """Get or create cached coordinate transformer."""
    if from_epsg == to_epsg:
        return None
    key = (from_epsg, to_epsg)
    if key not in _TRANSFORMER_CACHE:
        _TRANSFORMER_CACHE[key] = Transformer.from_crs(
            CRS.from_epsg(from_epsg),
            CRS.from_epsg(to_epsg),
            always_xy=True,
        )
    return _TRANSFORMER_CACHE[key]


def to_shapely(geom_input: Any) -> Optional[shapely.Geometry]:
    """
    Convert any geometry representation to a Shapely Geometry.
    Supports:
        - Shapely BaseGeometry / Geometry
        - GeoAlchemy2 WKBElement / WKTElement
        - Raw bytes (WKB / EWKB)
        - Hex strings (PostGIS EWKB hex)
        - WKT string
        - GeoJSON dictionary
    """
    if geom_input is None:
        return None

    if isinstance(geom_input, (shapely.Geometry, shapely.geometry.base.BaseGeometry)):
        return geom_input

    # GeoAlchemy2 WKBElement
    if WKBElement and isinstance(geom_input, WKBElement):
        try:
            return wkb.loads(bytes(geom_input.data))
        except Exception:
            return wkb.loads(bytes.fromhex(str(geom_input.data)))

    # GeoAlchemy2 WKTElement
    if WKTElement and isinstance(geom_input, WKTElement):
        return wkt.loads(str(geom_input.data))

    # Raw bytes (WKB)
    if isinstance(geom_input, (bytes, bytearray)):
        return wkb.loads(bytes(geom_input))

    # String (can be Hex-encoded EWKB, WKT, or JSON string)
    if isinstance(geom_input, str):
        str_val = geom_input.strip()
        if str_val.startswith("{"):
            try:
                parsed = json.loads(str_val)
                return shape(parsed)
            except Exception:
                pass
        # Try Hex WKB
        if re.match(r"^[0-9A-Fa-f]{8,}", str_val):
            try:
                # PostGIS hex EWKB can have SRID flag
                return wkb.loads(bytes.fromhex(str_val))
            except Exception:
                pass
        # Try WKT
        try:
            return wkt.loads(str_val)
        except Exception:
            pass

    # GeoJSON dict
    if isinstance(geom_input, dict):
        if "coordinates" in geom_input:
            return shape(geom_input)
        if "geometry" in geom_input and isinstance(geom_input["geometry"], dict):
            return shape(geom_input["geometry"])

    return None


def transform_geometry(
    geom: Any,
    from_epsg: Union[int, str] = 7755,
    to_epsg: Union[int, str] = 4326,
) -> Optional[shapely.Geometry]:
    """
    Transform geometry from source EPSG to target EPSG.
    """
    sh_geom = to_shapely(geom)
    if sh_geom is None:
        return None

    src_code = parse_crs(from_epsg)
    tgt_code = parse_crs(to_epsg)

    if src_code == tgt_code:
        return sh_geom

    t = get_transformer(src_code, tgt_code)
    if t is None:
        return sh_geom

    return transform(t.transform, sh_geom)


def geometry_to_geojson(
    geom: Any,
    source_epsg: Union[int, str] = 7755,
    target_epsg: Union[int, str] = 4326,
    precision: int = 7,
) -> Optional[Dict[str, Any]]:
    """
    Convert any geometry into a GeoJSON geometry dict in the target CRS.
    Default converts EPSG:7755 (SOI LCC) to EPSG:4326 (WGS84).
    """
    if geom is None:
        return None

    transformed = transform_geometry(geom, from_epsg=source_epsg, to_epsg=target_epsg)
    if transformed is None:
        return None

    mapped = mapping(transformed)
    
    # Optional coordinate rounding for clean GeoJSON
    def _round_coords(coords):
        if isinstance(coords, (list, tuple)):
            if len(coords) > 0 and isinstance(coords[0], (int, float)):
                return [round(c, precision) for c in coords]
            return [_round_coords(c) for c in coords]
        return coords

    if "coordinates" in mapped:
        mapped["coordinates"] = _round_coords(mapped["coordinates"])

    return mapped


def parse_bbox(
    bbox: Union[str, List[float], Tuple[float, ...]],
    bbox_crs: Union[int, str] = 4326,
    target_epsg: Union[int, str] = 7755,
) -> Optional[Tuple[float, float, float, float]]:
    """
    Parse a bounding box and reproject from bbox_crs to target_epsg.
    Returns (minx, miny, maxx, maxy) in target_epsg.
    """
    if not bbox:
        return None

    if isinstance(bbox, str):
        try:
            parts = [float(x.strip()) for x in bbox.split(",")]
        except ValueError:
            return None
    elif isinstance(bbox, (list, tuple)):
        parts = [float(x) for x in bbox]
    else:
        return None

    if len(parts) != 4:
        return None

    minx, miny, maxx, maxy = parts
    src_code = parse_crs(bbox_crs)
    tgt_code = parse_crs(target_epsg)

    if src_code == tgt_code:
        return (minx, miny, maxx, maxy)

    t = get_transformer(src_code, tgt_code)
    if t is None:
        return (minx, miny, maxx, maxy)

    # Transform lower-left and upper-right corners
    tx1, ty1 = t.transform(minx, miny)
    tx2, ty2 = t.transform(maxx, maxy)

    return (min(tx1, tx2), min(ty1, ty2), max(tx1, tx2), max(ty1, ty2))
