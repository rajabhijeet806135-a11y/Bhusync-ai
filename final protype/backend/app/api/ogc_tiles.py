"""
BhuSynch AI — OGC API Tiles (MVT) Endpoint
=============================================
Conforms to: OGC API – Tiles – Part 1: Core
Section 4, Row 5:
- GET /ogc/tiles — Available tile sets
- GET /ogc/tiles/parcels — TileJSON metadata for parcel vector tiles
- GET /ogc/tiles/parcels/{z}/{x}/{y}.pbf — Mapbox Vector Tiles (MVT)
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Request, Response

router = APIRouter(prefix="/ogc/tiles", tags=["OGC API – Tiles"])


@router.get("")
@router.get("/")
async def list_tilesets(request: Request):
    """
    OGC API – Tiles: List available tile sets.
    """
    base_url = str(request.base_url).rstrip("/")
    return {
        "tilesets": [
            {
                "id": "parcels",
                "title": "Harmonized Cadastral Parcels MVT",
                "dataType": "vector",
                "crs": "http://www.opengis.net/def/crs/EPSG/0/3857",
                "tileMatrixSetURI": "http://www.opengis.net/def/tms/EPSG/0/WebMercatorQuad",
                "links": [
                    {"rel": "self", "href": f"{base_url}/ogc/tiles/parcels", "type": "application/json"},
                    {"rel": "item", "href": f"{base_url}/ogc/tiles/parcels/{{z}}/{{x}}/{{y}}.pbf", "type": "application/vnd.mapbox-vector-tile"},
                ],
            }
        ],
        "links": [
            {"rel": "self", "href": f"{base_url}/ogc/tiles", "type": "application/json"},
        ],
    }


@router.get("/parcels")
async def get_tilejson_metadata(request: Request):
    """
    TileJSON 3.0.0 metadata for MapLibre GL / OpenLayers consumers.
    """
    base_url = str(request.base_url).rstrip("/")
    return {
        "tilejson": "3.0.0",
        "name": "BhuSynch Cadastral Parcels",
        "description": "High-density cadastral parcels for Pune Ward 14 in EPSG:7755/3857",
        "version": "1.0.0",
        "scheme": "xyz",
        "tiles": [f"{base_url}/ogc/tiles/parcels/{{z}}/{{x}}/{{y}}.pbf"],
        "minzoom": 12,
        "maxzoom": 22,
        "bounds": [73.850, 18.515, 73.865, 18.530],
        "center": [73.8567, 18.5204, 17],
        "vector_layers": [
            {
                "id": "parcels",
                "description": "Cadastral parcel boundaries with ULPIN and area",
                "fields": {
                    "ulpin": "String",
                    "khasra_no": "String",
                    "status": "String",
                    "legal_area_sqm": "Number",
                },
            }
        ],
    }


@router.get("/parcels/{z}/{x}/{y}.pbf")
async def get_parcel_mvt_tile(z: int, x: int, y: int):
    """
    OGC API – Tiles (MVT): Stream Mapbox Vector Tiles to MapLibre GL frontend.
    Proxies to Martin Tile Server when running; returns valid empty tile fallback when offline.
    """
    import httpx
    from app.config import settings

    try:
        martin_url = f"{settings.MARTIN_URL}/parcels/{z}/{x}/{y}.pbf"
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(martin_url)
            if response.status_code == 200:
                return Response(
                    content=response.content,
                    media_type="application/vnd.mapbox-vector-tile",
                    headers={
                        "Cache-Control": "public, max-age=3600",
                        "Access-Control-Allow-Origin": "*",
                    },
                )
            elif response.status_code == 204:
                return Response(content=b"", status_code=204)
    except Exception:
        pass

    # Martin server not connected — return valid empty 204 MVT response
    return Response(
        content=b"",
        status_code=204,
        media_type="application/vnd.mapbox-vector-tile",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=300",
        },
    )
