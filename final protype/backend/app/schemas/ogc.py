"""
BhuSynch AI — OGC API Standards Compliant Schemas
===================================================
Conforms to:
- OGC API – Features – Part 1: Core (1.0)
- OGC API – Features – Part 2: Coordinate Reference Systems by Reference (1.0)
- OGC API – Processes – Part 1: Core (1.0)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OGCLink(BaseModel):
    href: str
    rel: str
    type: Optional[str] = "application/geo+json"
    title: Optional[str] = None
    hreflang: Optional[str] = None


class OGCConformanceDeclaration(BaseModel):
    conformsTo: List[str] = Field(
        default=[
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/html",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
            "http://www.opengis.net/spec/ogcapi-features-2/1.0/conf/crs",
        ]
    )


class OGCSpatialExtent(BaseModel):
    bbox: List[List[float]] = Field(
        default_factory=lambda: [[73.80, 18.45, 73.95, 18.60]]  # Pune Urban Extent
    )
    crs: str = "http://www.opengis.net/def/crs/OGC/1.3/CRS84"


class OGCTemporalExtent(BaseModel):
    interval: List[List[Optional[str]]] = Field(
        default_factory=lambda: [["2024-01-01T00:00:00Z", None]]
    )
    trs: str = "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian"


class OGCExtent(BaseModel):
    spatial: Optional[OGCSpatialExtent] = Field(default_factory=OGCSpatialExtent)
    temporal: Optional[OGCTemporalExtent] = Field(default_factory=OGCTemporalExtent)


class OGCCollectionInfo(BaseModel):
    id: str
    title: str
    description: str = ""
    extent: Optional[OGCExtent] = Field(default_factory=OGCExtent)
    itemType: str = "feature"
    crs: List[str] = Field(
        default=[
            "http://www.opengis.net/def/crs/EPSG/0/7755",
            "http://www.opengis.net/def/crs/EPSG/0/4326",
            "http://www.opengis.net/def/crs/OGC/1.3/CRS84",
        ]
    )
    storageCrs: str = "http://www.opengis.net/def/crs/EPSG/0/7755"
    links: List[Dict[str, Any]] = Field(default_factory=list)


class OGCCollectionsResponse(BaseModel):
    collections: List[OGCCollectionInfo] = Field(default_factory=list)
    links: List[Dict[str, Any]] = Field(default_factory=list)
    crs: List[str] = Field(
        default=[
            "http://www.opengis.net/def/crs/EPSG/0/7755",
            "http://www.opengis.net/def/crs/EPSG/0/4326",
        ]
    )


class OGCFeature(BaseModel):
    type: str = "Feature"
    id: Optional[str] = None
    geometry: Optional[Dict[str, Any]] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    links: List[Dict[str, Any]] = Field(default_factory=list)


class OGCFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    numberMatched: int = 0
    numberReturned: int = 0
    features: List[OGCFeature] = Field(default_factory=list)
    links: List[Dict[str, Any]] = Field(default_factory=list)
    timeStamp: Optional[str] = None
