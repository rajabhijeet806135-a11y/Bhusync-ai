# BhuSynch AI — API Reference

> Complete OGC + REST API documentation for the National Urban Cadastral Intelligence Mesh

---

## Base URL

```
Production:  https://bhusynch.nic.in/api
Development: http://localhost:8000
```

## Authentication

All API endpoints require Keycloak OIDC JWT bearer tokens:

```http
Authorization: Bearer <jwt_token>
```

### Roles
| Role | Permissions |
|------|------------|
| `surveyor` | Read parcels, submit georef/conflation jobs |
| `revenue_officer` | All surveyor + adjudication + dossier generation |
| `admin` | Full access including audit verification |

---

## 1. OGC API — Features (Part 1 & 2)

### 1.1 List Parcels

```http
GET /ogc/features/collections/parcels/items
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `bbox` | string | Bounding box filter: `minLon,minLat,maxLon,maxLat` |
| `bbox-crs` | string | CRS of bbox coordinates (default: `EPSG:4326`) |
| `crs` | string | Response CRS (default: `EPSG:7755`) |
| `limit` | integer | Max results (default: 100, max: 1000) |
| `offset` | integer | Pagination offset |
| `status` | string | Filter by status: `PROVISIONAL`, `CANDIDATE`, `VERIFIED`, `ADJUDICATED` |
| `district_code` | string | Filter by district code |
| `village_code` | string | Filter by village code |

**Response:** `200 OK`

```json
{
  "type": "FeatureCollection",
  "numberReturned": 50,
  "numberMatched": 1234,
  "features": [
    {
      "type": "Feature",
      "id": "IN-MH-PNE-001234-0001",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[73.8567, 18.5204], ...]]
      },
      "properties": {
        "ulpin": "IN-MH-PNE-001234-0001",
        "parcel_id": "550e8400-e29b-41d4-a716-446655440000",
        "state_code": "MH",
        "district_code": "PNE",
        "village_code": "001234",
        "khasra_no": "123/4",
        "khata_no": "567",
        "legal_area_sqm": 2500.0000,
        "observed_area_sqm": 2487.3200,
        "status": "VERIFIED",
        "created_at": "2025-01-15T10:30:00Z",
        "updated_at": "2025-03-20T14:15:00Z"
      }
    }
  ],
  "links": [
    {"rel": "self", "href": "/ogc/features/collections/parcels/items?limit=50"},
    {"rel": "next", "href": "/ogc/features/collections/parcels/items?offset=50&limit=50"}
  ]
}
```

---

### 1.2 Get Parcel by ULPIN

```http
GET /ogc/features/collections/parcels/items/{ulpin}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `ulpin` | string | 14-character ULPIN (Bhu-Aadhaar) identifier |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `crs` | string | Response CRS (default: `EPSG:7755`) |
| `include_vertices` | boolean | Include vertex error ellipses (default: false) |
| `include_ownership` | boolean | Include ownership records (default: false) |
| `include_conflicts` | boolean | Include spatial conflicts (default: false) |

**Response:** `200 OK`

```json
{
  "type": "Feature",
  "id": "IN-MH-PNE-001234-0001",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[73.8567, 18.5204], ...]]
  },
  "properties": {
    "ulpin": "IN-MH-PNE-001234-0001",
    "parcel_id": "550e8400-e29b-41d4-a716-446655440000",
    "legal_area_sqm": 2500.0000,
    "observed_area_sqm": 2487.3200,
    "status": "VERIFIED",
    "vertices": [
      {
        "vertex_index": 0,
        "sigma_major_axis_m": 0.1200,
        "sigma_minor_axis_m": 0.0800,
        "orientation_deg": 45.50,
        "confidence_score": 0.945,
        "geometry": {"type": "Point", "coordinates": [73.8567, 18.5204]}
      }
    ],
    "ownership_records": [
      {
        "owner_name_vernacular": "राजेश कुमार शर्मा",
        "owner_name_english": "Rajesh Kumar Sharma",
        "share_fraction": "1/2",
        "land_type": "Bagayat",
        "ocr_confidence": 0.923
      }
    ],
    "conflicts": [
      {
        "conflict_type": "AREA_DISCREPANCY",
        "severity": "MEDIUM",
        "discrepancy_area_sqm": 12.6800,
        "adjudication_status": "PENDING_OFFICER_REVIEW"
      }
    ]
  }
}
```

---

## 2. OGC API — Processes (Async)

### 2.1 Trigger Georeferencing Pipeline

```http
POST /ogc/processes/georeference/execution
```

**Request Body:**

```json
{
  "inputs": {
    "legacy_map_url": "s3://bhusynch-maps/sajra_pune_001.tif",
    "drone_ori_url": "s3://bhusynch-drone/pune_ori_5cm.tif",
    "cors_stations": ["PUNE_CORS_01", "PUNE_CORS_02"],
    "source_crs": "EPSG:4243",
    "target_crs": "EPSG:7755",
    "tps_lambda": 0.1,
    "ransac_threshold": 5.0
  }
}
```

**Response:** `201 Created`

```json
{
  "jobID": "georef-job-abc123",
  "status": "accepted",
  "message": "Georeferencing pipeline submitted",
  "links": [
    {"rel": "status", "href": "/ogc/processes/georeference/jobs/georef-job-abc123"}
  ]
}
```

**Pipeline Steps:**
1. SuperPoint keypoint detection on both images
2. LightGlue cross-attention sparse matching
3. RANSAC GCP set filtering
4. 7-Parameter Helmert transformation
5. Thin-Plate Spline elastic warp
6. CORS constrained least-squares adjustment
7. Output: WGS84/EPSG:7755 GeoTIFF

---

### 2.2 Trigger Conflation Pipeline

```http
POST /ogc/processes/conflation/execution
```

**Request Body:**

```json
{
  "inputs": {
    "imagery_url": "s3://bhusynch-drone/pune_rgb_5cm.tif",
    "dsm_url": "s3://bhusynch-drone/pune_dsm.tif",
    "dtm_url": "s3://bhusynch-drone/pune_dtm.tif",
    "legacy_vectors_url": "s3://bhusynch-vectors/khasra_pune.geojson",
    "ndsm_threshold": 0.5,
    "frechet_gamma": 0.01,
    "dp_tolerance": 0.3
  }
}
```

**Response:** `201 Created`

```json
{
  "jobID": "conflation-job-xyz789",
  "status": "accepted",
  "message": "SAM-Geo conflation pipeline submitted",
  "links": [
    {"rel": "status", "href": "/ogc/processes/conflation/jobs/conflation-job-xyz789"}
  ]
}
```

**Pipeline Steps:**
1. 6-channel tensor preparation (RGB + DSM + DTM + nDSM)
2. SAM-Geo ViT-H boundary segmentation
3. Douglas-Peucker simplification + angle regularization
4. GIN/GNN Fréchet elastic graph matching
5. Hierarchical block-level ICP adjustment
6. Output: Harmonized parcel polygons + conflict cases

---

## 3. OGC API — Tiles (MVT)

### 3.1 Get Vector Tile

```http
GET /ogc/tiles/parcels/{z}/{x}/{y}.pbf
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `z` | integer | Zoom level (0-22) |
| `x` | integer | Tile column |
| `y` | integer | Tile row |

**Response:** `200 OK` with `Content-Type: application/vnd.mapbox-vector-tile`

Returns Mapbox Vector Tiles (MVT/PBF) for streaming to MapLibre GL frontend. Tiles are served via Martin tile server proxy.

**Layer Properties in Tile:**
- `ulpin` — Parcel ULPIN
- `status` — Parcel status
- `legal_area_sqm` — Legal area
- `has_conflict` — Boolean conflict flag
- `conflict_severity` — Conflict severity level

---

## 4. Custom REST API — Adjudication

### 4.1 Generate Statutory Dossier

```http
POST /api/v1/adjudication/dossier/{ulpin}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `ulpin` | string | 14-character ULPIN identifier |

**Request Body:**

```json
{
  "officer_id": "RO-MH-PNE-001",
  "include_conflict_analysis": true,
  "include_merkle_proof": true,
  "output_format": "PDF"
}
```

**Response:** `200 OK`

```json
{
  "dossier_url": "s3://bhusynch-dossiers/IN-MH-PNE-001234-0001_dossier.pdf",
  "ulpin": "IN-MH-PNE-001234-0001",
  "officer_id": "RO-MH-PNE-001",
  "generated_at": "2025-03-20T14:15:00Z",
  "dsc_signature": "MIIBojANBgkqhkiG9...",
  "sections": [
    "parcel_overview",
    "ownership_registry",
    "spatial_analysis",
    "conflict_cases",
    "merkle_provenance",
    "officer_recommendation"
  ]
}
```

**Dossier Contents:**
- Parcel overview with 3D visualization
- Complete ownership registry (all RoR records)
- Spatial analysis with vertex error ellipses
- Three-Truths conflict cases (A/B/C)
- Merkle hash chain provenance proof
- AI recommendation ("AI Proposes, Officer Disposes")

---

## 5. Custom REST API — Audit

### 5.1 Verify Merkle Hash Chain

```http
GET /api/v1/audit/verify/{ulpin}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `ulpin` | string | 14-character ULPIN identifier |

**Response:** `200 OK`

```json
{
  "ulpin": "IN-MH-PNE-001234-0001",
  "chain_valid": true,
  "chain_length": 15,
  "latest_hash": "a3f2b8c9d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
  "entries": [
    {
      "entry_id": 1,
      "event_type": "RECTIFICATION",
      "officer_id": "SO-MH-PNE-001",
      "timestamp": "2025-01-15T10:30:00Z",
      "prev_merkle_hash": "0000000000000000000000000000000000000000000000000000000000000000",
      "current_hash": "b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5",
      "hash_verified": true,
      "dsc_valid": true
    },
    {
      "entry_id": 2,
      "event_type": "MUTATION",
      "officer_id": "RO-MH-PNE-002",
      "timestamp": "2025-02-20T11:45:00Z",
      "prev_merkle_hash": "b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5",
      "current_hash": "c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
      "hash_verified": true,
      "dsc_valid": true
    }
  ]
}
```

**Hash Formula (SHA3-256):**
```
H_k = SHA3-256(ULPIN || Timestamp || Officer_ID || Geom_WKB || H_{k-1})
```

---

## 6. Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Parcel not found",
  "status_code": 404,
  "error_type": "NOT_FOUND"
}
```

| Status Code | Description |
|-------------|-------------|
| `400` | Bad Request — Invalid parameters |
| `401` | Unauthorized — Missing or invalid JWT |
| `403` | Forbidden — Insufficient role permissions |
| `404` | Not Found — Resource does not exist |
| `422` | Validation Error — Invalid request body |
| `500` | Internal Server Error |
| `503` | Service Unavailable — Worker queue full |

---

## 7. Interactive Documentation

When the backend is running, Swagger UI is available at:

```
http://localhost:8000/docs
```

ReDoc is available at:

```
http://localhost:8000/redoc
```
