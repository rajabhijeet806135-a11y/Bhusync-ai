# BhuSynch AI — Full Master Guide: Backend, Frontend & Deployment

> **National Urban Cadastral Intelligence Mesh**  
> *Automated Integration and Intelligent Harmonization of Multi-source Geospatial Data for Urban Land Record Management*  
> **Problem Statement ID:** SIH 26013 | **Standard Alignment:** NAKSHA (DoLR/MoRD), DILRMP, ULPIN, OGC Standards

---

## Table of Contents

1. [Executive Summary & High-Level Architecture](#1-executive-summary--high-level-architecture)
2. [Full Backend Architecture & Guide](#2-full-backend-architecture--guide)
   - [2.1 Backend Technology Stack](#21-backend-technology-stack)
   - [2.2 Directory Structure & Module Breakdown](#22-directory-structure--module-breakdown)
   - [2.3 Mathematical, Geodetic & AI Engines](#23-mathematical-geodetic--ai-engines)
   - [2.4 REST & OGC API Reference](#24-rest--ogc-api-reference)
   - [2.5 Database Schema & PostGIS Spatial Models](#25-database-schema--postgis-spatial-models)
   - [2.6 Step-by-Step Local Backend Setup (Windows & Linux/macOS)](#26-step-by-step-local-backend-setup-windows--linuxmacos)
   - [2.7 Celery Distributed Worker Setup](#27-celery-distributed-worker-setup)
   - [2.8 Testing & Benchmarking](#28-testing--benchmarking)
3. [Full Frontend Architecture & Guide](#3-full-frontend-architecture--guide)
   - [3.1 Frontend Technology Stack](#31-frontend-technology-stack)
   - [3.2 Directory Structure & Component Breakdown](#32-directory-structure--component-breakdown)
   - [3.3 Core Applications & User Portals](#33-core-applications--user-portals)
   - [3.4 Spatial Layers & 3D Visualization Pipeline](#34-spatial-layers--3d-visualization-pipeline)
   - [3.5 API Client & Graceful Offline Fallback Engine](#35-api-client--graceful-offline-fallback-engine)
   - [3.6 Step-by-Step Local Frontend Setup](#36-step-by-step-local-frontend-setup)
4. [Full Deployment Guide](#4-full-deployment-guide)
   - [4.1 Deployment Architecture & Multi-Service Topology](#41-deployment-architecture--multi-service-topology)
   - [4.2 Prerequisites & Hardware Sizing](#42-prerequisites--hardware-sizing)
   - [4.3 Environment Variables Reference (.env Checklist)](#43-environment-variables-reference-env-checklist)
   - [4.4 Local Development Deployment (Docker Compose Dev)](#44-local-development-deployment-docker-compose-dev)
   - [4.5 Production Containerized Deployment (Docker Compose)](#45-production-containerized-deployment-docker-compose)
   - [4.6 Cloud & Enterprise Deployment (Kubernetes / NIC MeghRaj)](#46-cloud--enterprise-deployment-kubernetes--nic-meghraj)
   - [4.7 NGINX Reverse Proxy, Security & SSL/TLS Hardening](#47-nginx-reverse-proxy-security--ssltls-hardening)
   - [4.8 Database Initialization & PostGIS 3.4 Setup](#48-database-initialization--postgis-34-setup)
   - [4.9 Object Storage (MinIO S3) Configuration](#49-object-storage-minio-s3-configuration)
   - [4.10 Martin Vector Tile Server Setup](#410-martin-vector-tile-server-setup)
   - [4.11 Identity & Access Management (Keycloak OIDC)](#411-identity--access-management-keycloak-oidc)
   - [4.12 Health Monitoring, Observability & Structured Logging](#412-health-monitoring-observability--structured-logging)
5. [Operational Troubleshooting & Runbook](#5-operational-troubleshooting--runbook)
6. [Quick Reference Command Matrix](#6-quick-reference-command-matrix)

---

## 1. Executive Summary & High-Level Architecture

**BhuSynch AI** addresses India's foundational cadastral challenge: the **"Three-Truths Problem"** in land administration:
1. **Legal Truth:** Textual Records of Rights (RoR / 7/12 extract / Jamabandi).
2. **Administrative Truth:** Historical hand-drawn cloth/paper village revenue maps (*Sajra* / *Cadastral Maps*).
3. **Physical Truth:** Real-world ground reality captured via high-resolution drone orthophotos (ORI), LiDAR, and satellite imagery.

Discrepancies among these three sources result in protracted land disputes, stalled infrastructure projects, and encumbered titles. BhuSynch AI creates an automated, mathematically rigorous, cryptographically auditable intelligence mesh to ingest, georeference, conflate, adjudicate, and publish harmonized cadastral parcels.

### High-Level System Architecture Diagram

```
                              ┌────────────────────────────────────────────────────────┐
                              │                    CLIENT TIER                         │
                              │  • 3D Web-GIS Console (MapLibre GL JS + Deck.gl)      │
                              │  • Statutory Adjudication Portal (DSC RSA-2048 Sign)   │
                              │  • Mobile Ground-Truthing PWA (GNSS RTK Geo-tagging)   │
                              └───────────────────────────┬────────────────────────────┘
                                                          │ HTTPS / WSS
                                                          ▼
                              ┌────────────────────────────────────────────────────────┐
                              │            REVERSE PROXY & GATEWAY TIER                │
                              │  • NGINX: SSL Termination, Rate Limiting, Gzip Caching │
                              │  • Keycloak: OIDC/OAuth2 Auth, RBAC (Collector/Officer)│
                              └─────────────┬────────────────────────────┬─────────────┘
                                            │                            │
                     ┌──────────────────────┴──────┐                     │ MVT Vector Tiles
                     ▼                             ▼                     ▼
┌──────────────────────────────────────────┐  ┌────────────────────────────────────────┐
│             API GATEWAY TIER             │  │            VECTOR TILE SERVER          │
│  FastAPI (Python 3.11+, Async, ORJSON)   │  │  Martin Tile Server (Rust)             │
│  • OGC API Features (Part 1 & 2)         │  │  • Streams MVT (.pbf) direct from      │
│  • OGC API Processes (Async Workflows)   │  │    PostGIS ST_AsMVT                    │
│  • OGC API Tiles Proxy                   │  │  • Port 3000                           │
│  • Statutory Adjudication REST API       │  └────────────────────────────────────────┘
│  • Merkle Audit Verification REST API    │
└────────────────────┬─────────────────────┘
                     │ Task Delegation
                     ▼
┌──────────────────────────────────────────┐  ┌────────────────────────────────────────┐
│            DISTRIBUTED BROKER            │  │          OBJECT STORAGE TIER           │
│  Redis 7 (In-Memory Broker & Cache)      │  │  MinIO (S3-Compatible Object Store)    │
│  • Queue: geodesy, geoai, conflation,    │  │  • Cloud-Optimized GeoTIFFs (COG)      │
│    document_ai, topology                 │  │  • Drone Orthomosaics & Sajra Scans    │
└────────────────────┬─────────────────────┘  └────────────────────────────────────────┘
                     │ Pull Tasks
                     ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                            GEOAI & MATHEMATICAL WORKER TIER                          │
│  Celery Distributed Workers (PyTorch, OpenCV, GDAL/Rasterio, Shapely, Scipy)         │
│  • Subsystem 1: Geodetic Ingestion & Helmert 7-Param + TPS Orthorectification        │
│  • Subsystem 2: GeoAI Feature Extraction (SAM-Geo, LightGlue Feature Matching)       │
│  • Subsystem 3: Multi-Source Conflation & Elastic Mesh Snapping (Fréchet / ICP)      │
│  • Subsystem 4: 7 Multi-Ministry Quality Gates & Topological Rule Validation         │
│  • Subsystem 5: Statutory Adjudication, SHA3-256 Merkle Ledger & Dossier Generation  │
└──────────────────────────────────────────┬───────────────────────────────────────────┘
                                           │ Read/Write Spatially Indexed Data
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                              PRIMARY DATA STORE TIER                                 │
│  PostgreSQL 16 + PostGIS 3.4 (Alpine Container)                                      │
│  • EPSG:7755 (Survey of India) + EPSG:4326 (WGS84) Geometries                        │
│  • GiST Spatial Indexing (parcels, conflicts, roads, waterbodies, surveyed points)   │
│  • Merkle DAG Nodes, Adjudication Signatures, Audit Log Ledger                       │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Full Backend Architecture & Guide

### 2.1 Backend Technology Stack

| Layer | Component | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Web Framework** | FastAPI | `>= 0.111.0` | Asynchronous high-performance REST & OGC API server |
| **ASGI Server** | Uvicorn (standard) | `>= 0.30.1` | Event-loop based production ASGI application server |
| **Serialization** | ORJSON / Pydantic v2 | `>= 2.7.4` | Ultra-fast JSON encoding and strict request/response data contracts |
| **Task Queue** | Celery + Redis | `>= 5.4.0` / 7-alpine | Distributed task processing for heavy AI/Geodetic workloads |
| **Database ORM & Driver** | SQLAlchemy + asyncpg | `>= 2.0.30` / `>= 0.29.0` | Asynchronous PostgreSQL/PostGIS connection pooling |
| **Computational Geometry**| Shapely + PyProj | `>= 2.0.4` / `>= 3.6.1` | Planar geometry, geodesy, and map projection transformations |
| **Numerical Math & Geodesy**| NumPy + SciPy | `>= 1.26.0` / `>= 1.13.0` | Least-Squares Adjustments, Helmert Matrix Algebra, Thin Plate Splines |
| **Computer Vision / AI** | OpenCV + Pillow | `>= 4.9.0` / `>= 10.3.0` | Image processing, GCP detection, corner-detection, raster parsing |
| **Deep Learning (Production)**| PyTorch + Segment Anything | Optional / Modular | SAM-Geo zero-shot boundary delineation and LightGlue feature matching |
| **Cryptography** | `cryptography` | `>= 42.0.8` | SHA3-256 cryptographic hashing, Merkle DAG computation, X.509 DSC validation |
| **Logging** | `structlog` | `>= 24.2.0` | Production JSON-structured logging with context tracing |

---

### 2.2 Directory Structure & Module Breakdown

The backend codebase resides in `backend/` and is organized as follows:

```
backend/
├── app/
│   ├── main.py                  # FastAPI application entrypoint, CORS, router mounting, lifespan hooks
│   ├── config.py                # Pydantic BaseSettings loading .env and defaults
│   ├── database.py              # Async database engine, sessionmaker, init_db, health checks
│   │
│   ├── api/                     # REST and OGC Standard API Routers
│   │   ├── adjudication.py      # Dispute resolution, conflict queries, multi-ministry benchmarks
│   │   ├── audit.py             # SHA3-256 Merkle chain verification and immutable audit history
│   │   ├── ogc_features.py      # OGC API - Features Part 1 & Part 2 endpoints
│   │   ├── ogc_processes.py     # OGC API - Processes execution & asynchronous job tracking
│   │   └── ogc_tiles.py         # OGC API - Tiles / Martin tile reverse proxy
│   │
│   ├── core/                    # Core Mathematical, Geodetic & Cryptographic Algorithms
│   │   ├── crs.py               # EPSG:7755 (SoI) ↔ EPSG:4326 (WGS84) pyproj coordinate transforms
│   │   ├── helmert.py           # 7-parameter 3D Bursa-Wolf / Helmert Geodetic Transformation
│   │   ├── tps.py               # Thin Plate Spline non-linear elastic warping engine
│   │   ├── lsa.py               # Least-Squares Network Adjustment for CORS baseline processing
│   │   ├── frechet.py           # Discrete Fréchet Distance calculation for boundary similarity
│   │   ├── ulpin.py             # 14-character statutory Bhu-Aadhaar / ULPIN generator
│   │   ├── merkle.py            # SHA3-256 Merkle Tree DAG engine for tamper-proof audit trails
│   │   └── dsc.py               # IT Act 2000 Section 35 Digital Signature Certificate (DSC) validator
│   │
│   ├── models/                  # Pydantic Schemas & SQLAlchemy 2.0 ORM Entities
│   │   ├── schemas.py           # GeoJSON FeatureCollection, AdjudicationPayload, AuditLog models
│   │   └── orm.py               # CadastralParcel, ConflictZone, MerkleNode, DisputeCase tables
│   │
│   └── workers/                 # Celery Asynchronous Pipeline
│       ├── celery_app.py        # Celery broker configuration, routing queues, concurrency settings
│       └── tasks.py             # Async worker tasks (georeference_task, conflation_task, audit_task)
│
├── requirements.txt             # Complete production dependencies
├── requirements-windows.txt     # Windows native developer dependencies (no complex C-compilers needed)
├── pyproject.toml               # Python project configuration & packaging metadata
└── Dockerfile                   # Multi-stage production container build
```

---

### 2.3 Mathematical, Geodetic & AI Engines

#### 1. 7-Parameter Helmert Coordinate Transformation (`app/core/helmert.py`)
Converts local or historical geodetic coordinates to the national datum (**EPSG:7755** / Survey of India). It solves for 3 translations $(\Delta X, \Delta Y, \Delta Z)$, 3 rotations $(R_X, R_Y, R_Z)$, and a scale factor $(s)$:

$$\begin{bmatrix} X_{target} \\ Y_{target} \\ Z_{target} \end{bmatrix} = \begin{bmatrix} \Delta X \\ \Delta Y \\ \Delta Z \end{bmatrix} + (1 + s \times 10^{-6}) \begin{bmatrix} 1 & -R_Z & R_Y \\ R_Z & 1 & -R_X \\ -R_Y & R_X & 1 \end{bmatrix} \begin{bmatrix} X_{source} \\ Y_{source} \\ Z_{source} \end{bmatrix}$$

#### 2. Thin Plate Spline (TPS) Elastic Warping (`app/core/tps.py`)
Used for non-linear orthorectification of distorted hand-drawn revenue maps (*Sajra*). Given Ground Control Points (GCPs), it minimizes bending energy to warp historical map features without introducing local folding:

$$E_{tps}(f) = \iint_{\mathbb{R}^2} \left[ \left(\frac{\partial^2 f}{\partial x^2}\right)^2 + 2\left(\frac{\partial^2 f}{\partial x \partial y}\right)^2 + \left(\frac{\partial^2 f}{\partial y^2}\right)^2 \right] dx \, dy$$

#### 3. CORS Least-Squares Adjustment (LSA) (`app/core/lsa.py`)
Processes baseline vectors from Survey of India Continuously Operating Reference Stations (CORS). It computes the normal equations:

$$\mathbf{\hat{x}} = (\mathbf{A}^T \mathbf{P} \mathbf{A})^{-1} \mathbf{A}^T \mathbf{P} \mathbf{l}$$

where $\mathbf{A}$ is the design matrix, $\mathbf{P}$ is the weight matrix (inverse covariance of GNSS observations), and $\mathbf{l}$ is the misclosure vector, generating the **95% Confidence Error Ellipses** displayed in the UI ($\pm 5\text{ cm}$).

#### 4. Discrete Fréchet Distance & ICP Conflation (`app/core/frechet.py`)
Quantifies boundary agreement between legal boundaries and drone physical fence lines. If Fréchet distance $\delta_F(P, Q) \le \epsilon$ (threshold $\le 15\text{ cm}$), boundaries auto-conflate; if $\delta_F > \epsilon$, a spatial conflict polygon is created.

#### 5. Statutory ULPIN (Bhu-Aadhaar) Generator (`app/core/ulpin.py`)
Computes the national 14-character alphanumeric Unique Land Parcel Identification Number based on the parcel centroid coordinates formatted under DoLR guidelines:

$$\text{ULPIN} = \mathcal{F}(\text{Latitude}_{EPSG:4326}, \text{Longitude}_{EPSG:4326}, \text{StateCode}, \text{LGD\_Code})$$

#### 6. SHA3-256 Merkle DAG Audit Ledger (`app/core/merkle.py`)
Guarantees evidentiary immutability under the Indian Evidence Act Section 65B. Every parcel edit, adjudication resolution, or DSC signature generates a cryptographic leaf node:

$$H_{\text{leaf}} = \text{SHA3-256}(\text{ULPIN} \parallel \text{OfficerID} \parallel \text{Timestamp} \parallel \text{Polygon\_WKT} \parallel \text{PrevHash})$$

---

### 2.4 REST & OGC API Reference

| Standard / Domain | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **System** | `GET` | `/` | Service identification, version, governance status |
| **System** | `GET` | `/health` | Deep health check (DB, Redis, Models connectivity) |
| **OGC Features** | `GET` | `/ogc/features/collections` | List available spatial feature collections |
| **OGC Features** | `GET` | `/ogc/features/collections/parcels/items` | Query cadastral parcels by bbox, limit, CRS |
| **OGC Features** | `GET` | `/ogc/features/collections/parcels/items/{ulpin}`| Retrieve single parcel feature by ULPIN |
| **OGC Features** | `GET` | `/ogc/features/collections/conflicts/items` | Query spatial overlap/encroachment conflicts |
| **OGC Processes**| `GET` | `/ogc/processes` | List registered async geospatial processing tasks |
| **OGC Processes**| `POST`| `/ogc/processes/georeference/execution` | Trigger async Sajra georeferencing job |
| **OGC Processes**| `POST`| `/ogc/processes/conflation/execution` | Trigger async drone + cadastral conflation job |
| **OGC Processes**| `GET` | `/ogc/processes/{job_id}/status` | Check status of async background job |
| **OGC Tiles** | `GET` | `/ogc/tiles/parcels/{z}/{x}/{y}.pbf` | Reverse proxy to Martin Mapbox Vector Tiles |
| **Adjudication** | `GET` | `/api/v1/adjudication/conflicts` | List active dispute cases with severity |
| **Adjudication** | `GET` | `/api/v1/adjudication/conflicts/{id}` | Detailed conflict geometry & ownership info |
| **Adjudication** | `POST`| `/api/v1/adjudication/adjudicate` | Execute dispute resolution with DSC signature |
| **Adjudication** | `POST`| `/api/v1/adjudication/dossier/{ulpin}` | Generate legal Dossier PDF with QR and Merkle seal |
| **Benchmark** | `GET` | `/api/v1/adjudication/multi-ministry-benchmark/{ulpin}` | Run 7 multi-ministry quality gates validation |
| **Audit** | `GET` | `/api/v1/audit/verify/{ulpin}` | Validate SHA3-256 Merkle chain integrity |
| **Audit** | `GET` | `/api/v1/audit/history/{ulpin}` | Retrieve complete immutable audit history logs |

Interactive OpenAPI documentation is accessible at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

### 2.5 Database Schema & PostGIS Spatial Models

The schema uses PostgreSQL 16 with the **PostGIS 3.4** extension enabled. All spatial columns are indexed using Generalized Search Trees (**GiST**).

```sql
-- 1. Enable PostGIS and UUID Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Cadastral Parcels Table
CREATE TABLE cadastral_parcels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ulpin VARCHAR(14) UNIQUE NOT NULL,
    state_code VARCHAR(2) NOT NULL,
    district_lgd INT NOT NULL,
    village_lgd INT NOT NULL,
    khasra_no VARCHAR(50) NOT NULL,
    legal_area_sqm NUMERIC(12, 4) NOT NULL,
    gis_area_sqm NUMERIC(12, 4) NOT NULL,
    area_discrepancy_pct NUMERIC(5, 2) GENERATED ALWAYS AS (
        ROUND(ABS(legal_area_sqm - gis_area_sqm) / legal_area_sqm * 100, 2)
    ) STORED,
    owner_name VARCHAR(255) NOT NULL,
    ownership_type VARCHAR(50) DEFAULT 'Private',
    geom_7755 GEOMETRY(MultiPolygon, 7755) NOT NULL,
    geom_4326 GEOMETRY(MultiPolygon, 4326) NOT NULL,
    confidence_ellipse_semi_major NUMERIC(6, 3) DEFAULT 0.05,
    confidence_ellipse_semi_minor NUMERIC(6, 3) DEFAULT 0.03,
    status VARCHAR(30) DEFAULT 'Validated',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_parcels_geom_7755 ON cadastral_parcels USING GIST (geom_7755);
CREATE INDEX idx_parcels_geom_4326 ON cadastral_parcels USING GIST (geom_4326);
CREATE INDEX idx_parcels_ulpin ON cadastral_parcels (ulpin);

-- 3. Spatial Conflicts Table
CREATE TABLE spatial_conflicts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conflict_code VARCHAR(50) UNIQUE NOT NULL,
    conflict_type VARCHAR(50) NOT NULL, -- 'Encroachment', 'Overlap', 'AreaDiscrepancy'
    severity VARCHAR(20) NOT NULL,      -- 'Critical', 'Warning', 'Informational'
    primary_ulpin VARCHAR(14) REFERENCES cadastral_parcels(ulpin),
    secondary_ulpin VARCHAR(14),
    disputed_area_sqm NUMERIC(10, 4) NOT NULL,
    dispute_geom GEOMETRY(Polygon, 4326) NOT NULL,
    status VARCHAR(30) DEFAULT 'Pending_Adjudication',
    detected_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_conflicts_geom ON spatial_conflicts USING GIST (dispute_geom);

-- 4. Merkle Audit Ledger Table
CREATE TABLE merkle_audit_ledger (
    id BIGSERIAL PRIMARY KEY,
    ulpin VARCHAR(14) NOT NULL,
    action VARCHAR(50) NOT NULL,
    officer_id VARCHAR(100) NOT NULL,
    dsc_cert_fingerprint VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    current_hash VARCHAR(64) NOT NULL,
    merkle_root VARCHAR(64) NOT NULL,
    payload_snapshot JSONB NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_merkle_ulpin ON merkle_audit_ledger (ulpin);
```

---

### 2.6 Step-by-Step Local Backend Setup (Windows & Linux/macOS)

#### Step 1: Open Terminal & Navigate to Project
**Windows (PowerShell):**
```powershell
cd C:\Users\rajab\Desktop\website\backend
```
**Linux / macOS:**
```bash
cd /path/to/website/backend
```

#### Step 2: Create and Activate a Python Virtual Environment
**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(Note: If PowerShell complains about script execution, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Backend Dependencies
- **For Rapid Windows Local Testing (Zero C-compiler issues):**
  ```powershell
  pip install --upgrade pip
  pip install -r requirements-windows.txt
  ```
- **For Full Linux / Docker / Production Environments:**
  ```bash
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

#### Step 4: Configure Environment File
Copy or create a `.env` file in the project root:
```env
APP_NAME=BhuSynch AI
APP_VERSION=1.0.0
DEBUG=True
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:8080,http://localhost:3000,http://127.0.0.1:8080,http://127.0.0.1:5500,http://localhost
DATABASE_URL=postgresql+asyncpg://bhusynch:bhusynch_pass@localhost:5432/bhusynch_cadastral
REDIS_URL=redis://:bhusynch_redis@localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ROOT_USER=bhusynch_minio
MINIO_ROOT_PASSWORD=bhusynch_secure_minio_2026
MARTIN_URL=http://localhost:3000
```

#### Step 5: Start the Backend Server
```bash
# Direct Python CLI launch
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
You will see:
```text
INFO:     Started server process [1234]
INFO:     Waiting for application startup.
INFO:     bhusynch_starting version=1.0.0
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```
Verify by visiting `http://localhost:8000/health` in your browser.

---

### 2.7 Celery Distributed Worker Setup

When running asynchronous georeferencing, conflation, or heavy computer vision tasks:

1. Ensure Redis is running locally or via Docker:
   ```bash
   docker run -d --name bhusynch-redis -p 6379:6379 redis:7-alpine
   ```
2. Start the Celery Worker from `backend/`:
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info --concurrency=4 -Q geodesy,geoai,document_ai,conflation,topology
   ```

---

### 2.8 Testing & Benchmarking

Execute the test suite from the `backend/` directory:
```bash
# Run all unit and integration tests
pytest -v

# Run with coverage report
pytest --cov=app tests/

# Run authentic data integration benchmarks
python generate_authentic_west_bengal_multi_ministry_suite.py
```

---

## 3. Full Frontend Architecture & Guide

### 3.1 Frontend Technology Stack

| Component | Library / Spec | Version / Source | Purpose |
| :--- | :--- | :--- | :--- |
| **Map Rendering Engine** | MapLibre GL JS | `v4.1.2` (CDN/Vendored) | 60 FPS GPU-accelerated vector & raster 3D map canvas |
| **3D Visualization Layer**| Deck.gl | `v8.9.35` (CDN/Vendored) | High-volume point cloud & 3D building polygon extrusions |
| **UI Architecture** | Vanilla HTML5 / ES6+ Modules | Standard | Maximum execution speed, zero node_modules build overhead |
| **Typography** | Inter & Outfit Font Family | Google Fonts | Crisp, high-contrast, modern government portal typography |
| **Theme & Styling** | Custom CSS3 System | Tailored | Dark theme, glassmorphic HUD overlays, responsive flex/grid |
| **Icons** | Phosphor Icons / Lucide SVG | Embedded | Lightweight SVG iconography for spatial tools |
| **State Management** | Modular JS Controllers | Native | Event-driven pub/sub communication across map and inspectors |

---

### 3.2 Directory Structure & Component Breakdown

The frontend codebase is located in `frontend/`:

```
frontend/
├── index.html                   # Primary 3D Web-GIS Cadastral Mesh Explorer
├── adjudication.html            # Quasi-Judicial Dispute Adjudication & Resolution Portal
│
├── css/
│   ├── main.css                 # Core design system tokens, typography, CSS reset, layout
│   ├── map.css                  # MapLibre container styles, Deck.gl canvas overlay, custom crosshairs
│   ├── sidebar.css              # Left-hand layer manager, filters, collapsible accordion styling
│   ├── inspector.css            # Right-hand Cadastral Inspector panel, RoR cards, variance badges
│   └── adjudication.css         # Adjudication console, split-map swipe viewer, DSC signature modal
│
├── js/
│   ├── app.js                   # Application bootstrap, navigation, global event dispatching
│   ├── map-engine.js            # MapLibre GL wrapper: initialization, pitch/bearing, camera presets
│   ├── parcel-inspector.js      # ULPIN search, parcel selection, attribute display, RoR comparison
│   ├── adjudication-controller.js# Adjudication logic, swipe comparison, DSC signing, dossier generation
│   ├── api-client.js            # REST/OGC client with automatic offline fallback data handlers
│   │
│   ├── layers/                  # Spatial Layer Renderers
│   │   ├── cadastral-layer.js   # Green vector boundaries, fill opacity, line styling, hover glow
│   │   ├── drone-layer.js       # High-resolution orthomosaic imagery raster source & tiles
│   │   ├── conflict-layer.js    # Amber/Red hatched polygon overlay for overlaps and encroachments
│   │   └── uncertainty-layer.js # SVG/Canvas rendering of 95% confidence covariance error ellipses
│   │
│   └── utils/                   # Helper Utilities
│       ├── geo-calc.js          # Client-side area calculation, Haversine distance, perimeter metrics
│       ├── formatters.js        # Area conversions (Sq.m ↔ Bigha ↔ Gunta ↔ Acres), ULPIN formatting
│       └── export.js            # GeoJSON, KML, and SVG snapshot exports
│
└── data/                        # Statewide Authentic Data & Offline Fallback Records
    ├── statewide_west_bengal_ror_records.json
    ├── west_bengal_districts_cadastral_summary.json
    ├── west_bengal_official_cadastral_features.geojson
    ├── authentic_west_bengal_dispute_cases.geojson
    └── official_west_bengal_quality_benchmarks.json
```

---

### 3.3 Core Applications & User Portals

The frontend delivers two primary web applications:

#### 1. 3D Web-GIS Cadastral Mesh Explorer (`frontend/index.html`)
- **Map Viewport:** 3D tilted view (pitch: 45°, bearing: -15°) rendering cadastral polygons with interactive selection.
- **Layer Control Toolbar:** Toggle between Cadastral Parcels, Drone Orthophoto, Historical Sajra Maps, Satellite Basemap, and Spatial Conflict Overlays.
- **Cadastral Inspector Panel:**
  - Displays 14-character ULPIN with copy-to-clipboard functionality.
  - Side-by-side comparison of **Legal Area** (RoR) vs. **GIS Computed Area**.
  - Automatic variance indicator: Green ($\le 2\%$), Yellow ($2\% - 5\%$), Red ($> 5\%$).
  - Land classification, owner details, Khasra/Dag numbers, and encumbrance status.
- **Search & Filter:** Search by ULPIN, Khasra Number, Owner Name, or District/Ward.

#### 2. Statutory Adjudication Portal (`frontend/adjudication.html`)
- **Split-Screen Swipe Viewer:** Interactive comparison swipe bar between Historical Sajra Map / Cadastral Vector vs. Current Drone Orthophoto.
- **Conflict Management Queue:** Filter conflicts by Critical, Warning, or Informational status.
- **Resolution Strategy Matrix:**
  1. *Accept Physical Ground Reality:* Realign boundary to physical drone fence line.
  2. *Enforce Legal Document Boundary:* Retain legal RoR coordinates; flag encroachment for eviction.
  3. *Proportional Compromise (Equitable Split):* Compute spatial midpoint using Least-Squares boundary shift.
- **Digital Signature Certificate (DSC) Integration:** Simulates IT Act 2000 Section 35 RSA-2048 compliant signing by the Revenue Officer / Settlement Officer.
- **Cryptographic Audit Ledger Verification:** Instantly visualizes the Merkle Tree path and verifies SHA3-256 leaf hashes.
- **Statutory Legal Dossier Generation:** Produces a printable adjudication report complete with embedded QR code, geo-coordinates, and tamper-evident cryptographic stamp.

---

### 3.4 Spatial Layers & 3D Visualization Pipeline

```
[ Topmost HUD ]      Hover Tooltips, Crosshair Coordinates, Measure Labels
       ▲
[ 3D Deck.gl ]       Building Mass Extrusions, 95% Confidence Covariance Ellipses
       ▲
[ Conflict Layer ]   Hatched Red/Amber Polygons (ST_Intersection Overlaps)
       ▲
[ Cadastral Mesh ]   Harmonized Green Vector Parcels (MapLibre GeoJSON/MVT)
       ▲
[ Historical Sajra ] Semi-transparent Georeferenced Historical Raster Overlay
       ▲
[ Drone Orthophoto ] High-Resolution RGB Imagery Tiles (COG / TileServer)
       ▲
[ Basemap ]          Satellite / OpenStreetMap / CartoDB Dark Vector Canvas
```

---

### 3.5 API Client & Graceful Offline Fallback Engine

The frontend's `js/api-client.js` is designed with **dual-mode resilience**:
1. **Live Backend Connected:** When `http://localhost:8000` is active, it queries live OGC Feature collections, executes server-side adjudication, and streams vector tiles from Martin.
2. **Standalone / Offline Mode:** If the backend is unreachable or offline, `api-client.js` gracefully intercepts errors and routes queries to rich local JSON/GeoJSON files in `frontend/data/`.

This ensures that the user interface, 3D map, search filters, conflict inspections, and demo adjudication workflows function seamlessly during client demonstrations or offline field deployments.

---

### 3.6 Step-by-Step Local Frontend Setup

Because the frontend is built using standard web standards, no complex build process (`npm install` or webpack/vite bundles) is required.

#### Method A: Using Python Built-in HTTP Server (Recommended)
Open a terminal in the `frontend/` directory:
```powershell
cd C:\Users\rajab\Desktop\website\frontend
python -m http.server 8080
```
Open your browser and navigate to:
- **Cadastral Mesh Explorer:** `http://localhost:8080/index.html`
- **Adjudication Portal:** `http://localhost:8080/adjudication.html`

#### Method B: Using Node.js `npx serve`
```bash
cd frontend
npx -y serve -l 8080 .
```

#### Method C: Using VSCode / IDE Live Server
Right-click on `frontend/index.html` in VSCode / Antigravity IDE and select **"Open with Live Server"**.

---

## 4. Full Deployment Guide

### 4.1 Deployment Architecture & Multi-Service Topology

The production setup runs as a containerized stack orchestrated by Docker Compose or Kubernetes:

| Service Name | Container Image | Port | Description |
| :--- | :--- | :--- | :--- |
| `bhusynch-postgres` | `postgis/postgis:16-3.4-alpine` | `5432` | Primary spatial database with PostGIS 3.4 |
| `bhusynch-redis` | `redis:7-alpine` | `6379` | In-memory message broker for Celery and caching |
| `bhusynch-minio` | `minio/minio:latest` | `9000, 9001`| S3-compatible object store for COG imagery and PDFs |
| `bhusynch-martin` | `ghcr.io/maplibre/martin:latest`| `3000` | Rust-based high-performance MVT vector tile server |
| `bhusynch-keycloak`| `quay.io/keycloak/keycloak:24.0`| `8080` | OIDC & OAuth2 identity and access management |
| `bhusynch-api` | Built from `backend/Dockerfile` | `8000` | FastAPI OGC and REST API gateway |
| `bhusynch-worker` | Built from `backend/Dockerfile` | Internal | Celery asynchronous worker pool |
| `bhusynch-frontend`| Built from `deployment/Dockerfile.frontend` | `80, 443` | NGINX serving static files and acting as reverse proxy |

---

### 4.2 Prerequisites & Hardware Sizing

#### Software Prerequisites
- **Docker Engine:** `24.0+`
- **Docker Compose:** `v2.20+`
- **Git:** `2.40+`
- **Kubernetes (for Cloud):** `1.28+` (`kubectl` configured)

#### Hardware Sizing Specifications

| Deployment Tier | Environment | vCPU | RAM | Disk Storage | GPU / Accelerators |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Local Developer** | Laptop / Workstation | 4 cores | 16 GB | 50 GB NVMe | Optional (CUDA) |
| **State Pilot (Single District)** | Virtual Machine | 8 cores | 32 GB | 250 GB SSD | 1× NVIDIA T4 (16GB) |
| **National Production (NIC MeghRaj)** | Cloud Cluster | 32 cores | 128 GB | 2 TB Distributed NVMe | 4× NVIDIA A10G / L4 |

---

### 4.3 Environment Variables Reference (.env Checklist)

Create a file named `.env` in the root of the project:

```env
# ── Common Configuration ──
TZ=Asia/Kolkata
APP_NAME=BhuSynch AI
APP_VERSION=1.0.0
DEBUG=false

# ── PostgreSQL & PostGIS ──
POSTGRES_DB=bhusynch_cadastral
POSTGRES_USER=bhusynch
POSTGRES_PASSWORD=bhusynch_secure_db_password_2026
POSTGRES_PORT=5432

# ── Redis ──
REDIS_PASSWORD=bhusynch_redis_auth_token_2026
REDIS_PORT=6379

# ── MinIO S3 Object Store ──
MINIO_ROOT_USER=bhusynch_minio_admin
MINIO_ROOT_PASSWORD=bhusynch_minio_secret_key_2026
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001

# ── Martin Tile Server ──
MARTIN_PORT=3000

# ── Keycloak Identity ──
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=bhusynch_keycloak_admin_2026
KEYCLOAK_PORT=8080

# ── Backend API & Celery ──
API_PORT=8000
CORS_ORIGINS=http://localhost,http://localhost:80,http://localhost:8080,https://bhusynch.gov.in

# ── Frontend Web Server ──
FRONTEND_PORT=80
```

---

### 4.4 Local Development Deployment (Docker Compose Dev)

The file `deployment/docker-compose.dev.yml` mounts local folders as volumes for hot-reloading code without rebuilding containers:

```bash
# Start development stack in background
docker compose -f deployment/docker-compose.dev.yml up -d

# Follow API logs in real-time
docker compose -f deployment/docker-compose.dev.yml logs -f api

# Stop development stack
docker compose -f deployment/docker-compose.dev.yml down
```

---

### 4.5 Production Containerized Deployment (Docker Compose)

From the project root directory:

```bash
# 1. Build and launch all 7 services in detached mode
docker compose -f deployment/docker-compose.yml up -d --build

# 2. Verify all container health statuses
docker compose -f deployment/docker-compose.yml ps

# Expected output:
# NAME                IMAGE                          STATUS                    PORTS
# bhusynch-postgres   postgis/postgis:16-3.4-alpine  Up (healthy)              0.0.0.0:5432->5432/tcp
# bhusynch-redis      redis:7-alpine                 Up (healthy)              0.0.0.0:6379->6379/tcp
# bhusynch-minio      minio/minio:latest             Up (healthy)              0.0.0.0:9000-9001->9000-9001/tcp
# bhusynch-martin     ghcr.io/maplibre/martin        Up                        0.0.0.0:3000->3000/tcp
# bhusynch-keycloak   quay.io/keycloak/keycloak:24.0 Up                        0.0.0.0:8080->8080/tcp
# bhusynch-api        bhusynch-api                   Up (healthy)              0.0.0.0:8000->8000/tcp
# bhusynch-worker     bhusynch-worker                Up                        
# bhusynch-frontend   bhusynch-frontend              Up                        0.0.0.0:80->80/tcp
```

To stop the entire production cluster:
```bash
docker compose -f deployment/docker-compose.yml down
```

To stop and erase all data volumes (Caution: Deletes DB data):
```bash
docker compose -f deployment/docker-compose.yml down -v
```

---

### 4.6 Cloud & Enterprise Deployment (Kubernetes / NIC MeghRaj)

All Kubernetes deployment manifests are maintained in `deployment/k8s/`:

```
deployment/k8s/
├── namespace.yaml                # Creates 'bhusynch' dedicated namespace
├── postgres-statefulset.yaml     # 16-3.4 PostGIS StatefulSet with PersistentVolumeClaim
├── redis-deployment.yaml         # Redis master deployment and ClusterIP service
├── minio-statefulset.yaml        # S3 distributed object storage
├── martin-deployment.yaml        # Vector tile streaming pods
├── keycloak-deployment.yaml      # OIDC identity server
├── api-deployment.yaml           # FastAPI horizontal autoscaling deployment (HPA)
├── worker-deployment.yaml        # Celery GPU/CPU worker pods
└── ingress.yaml                  # Ingress routing, TLS secret reference, rate limits
```

#### Step-by-Step Kubernetes Deployment Instructions:

```bash
# 1. Create the dedicated namespace
kubectl apply -f deployment/k8s/namespace.yaml

# 2. Create database and redis stateful backends
kubectl apply -f deployment/k8s/postgres-statefulset.yaml
kubectl apply -f deployment/k8s/redis-deployment.yaml
kubectl apply -f deployment/k8s/minio-statefulset.yaml

# 3. Wait for database pod to become ready
kubectl rollout status statefulset/postgres -n bhusynch --timeout=120s

# 4. Deploy the application tiers
kubectl apply -f deployment/k8s/martin-deployment.yaml
kubectl apply -f deployment/k8s/keycloak-deployment.yaml
kubectl apply -f deployment/k8s/api-deployment.yaml
kubectl apply -f deployment/k8s/worker-deployment.yaml

# 5. Apply Ingress Controller (NGINX Ingress / NIC MeghRaj Gateway)
kubectl apply -f deployment/k8s/ingress.yaml

# 6. Verify all pods are running
kubectl get pods -n bhusynch -o wide
```

---

### 4.7 NGINX Reverse Proxy, Security & SSL/TLS Hardening

The file `deployment/nginx/default.conf` provides enterprise routing and defense-in-depth:

```nginx
# Upstream definitions with keepalive connections
upstream api_backend {
    server api:8000;
    keepalive 32;
}

upstream martin_tiles {
    server martin:3000;
    keepalive 16;
}

server {
    listen 80;
    server_name bhusynch.gov.in;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://unpkg.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: https://*.tile.openstreetmap.org;" always;

    # API Proxy
    location /api/ {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # OGC Features & Processes Proxy
    location /ogc/ {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Vector Tiles Proxy (Martin)
    location /tiles/ {
        proxy_pass http://martin_tiles/;
        proxy_cache_valid 200 1d;
        proxy_set_header Host $host;
    }

    # Static Frontend
    location / {
        root /usr/share/nginx/html;
        index index.html adjudication.html;
        try_files $uri $uri/ /index.html;
    }
}
```

---

### 4.8 Database Initialization & PostGIS 3.4 Setup

When the PostgreSQL container starts for the first time, Docker automatically executes files placed inside `/docker-entrypoint-initdb.d/`.

The repository's `sql/init.sql` script:
1. Installs spatial and cryptographic extensions: `postgis`, `postgis_topology`, `uuid-ossp`.
2. Sets up Spatial Reference Systems: confirms **EPSG:7755** (Survey of India) and **EPSG:4326** (WGS84).
3. Creates partitioned tables for parcels, disputes, and Merkle ledger logs.
4. Generates spatial GiST indexes for millisecond bounding box queries.

To manually re-run or inspect the database:
```bash
docker exec -it bhusynch-postgres psql -U bhusynch -d bhusynch_cadastral
```

---

### 4.9 Object Storage (MinIO S3) Configuration

MinIO hosts Cloud-Optimized GeoTIFFs (COG) for drone orthomosaics:
- **Web Console:** `http://localhost:9001`
- **S3 API:** `http://localhost:9000`
- **Default Buckets Created:**
  - `drone-imagery`: High-resolution orthomosaic rasters (.tif, .cog)
  - `sajra-scans`: High-resolution historical cloth/paper map scans (.png, .jp2)
  - `adjudication-dossiers`: Statutory PDF dossiers with Merkle seals

---

### 4.10 Martin Vector Tile Server Setup

Martin connects directly to PostgreSQL and generates Mapbox Vector Tiles (.pbf) on-the-fly without needing any intermediate tile caching service:
- **Connection String:** `postgres://bhusynch:${POSTGRES_PASSWORD}@postgres:5432/bhusynch_cadastral`
- **Tile URL Scheme:** `http://localhost:3000/cadastral_parcels/{z}/{x}/{y}`
- **Tile Format:** Protocol Buffers (.pbf), automatically consumed by MapLibre GL JS `addSource('parcels', { type: 'vector', ... })`.

---

### 4.11 Identity & Access Management (Keycloak OIDC)

Configured for Role-Based Access Control (RBAC):
- **Realm:** `bhusynch`
- **Roles:**
  - `Revenue_Officer`: Can view parcels, inspect conflicts, execute statutory adjudications, sign DSC certificates.
  - `Surveyor_Field_Worker`: Can upload GNSS ground-truth GCP points and field observations.
  - `Citizen_Viewer`: Read-only access to harmonized public cadastral maps and ULPIN records.

---

### 4.12 Health Monitoring, Observability & Structured Logging

#### Structured JSON Logging
All backend events are emitted via `structlog` in JSON format:
```json
{"event": "adjudication_executed", "ulpin": "27-583-0012-0045", "officer_id": "OFFICER-MH-PN-401", "action": "ACCEPT_PHYSICAL", "level": "info", "timestamp": "2026-09-07T14:10:00Z"}
```

#### Health Check Endpoints
- **API Health:** `GET http://localhost:8000/health`
- **NGINX Health:** `GET http://localhost/health`
- **Postgres Health:** `pg_isready -U bhusynch -d bhusynch_cadastral`
- **Redis Health:** `redis-cli ping`

---

## 5. Operational Troubleshooting & Runbook

### Issue 1: `ImportError: DLL load failed` or GDAL / GEOS issues on Windows
- **Cause:** Native C-libraries for GDAL/Rasterio often fail on standard Windows Python installations without pre-compiled wheels.
- **Solution:** Use the provided lightweight dependencies file:
  ```powershell
  pip install -r requirements-windows.txt
  ```
  This uses pure-Python Shapely 2.0+ and PyProj pre-compiled wheels, avoiding GDAL system compilation entirely.

---

### Issue 2: CORS (Cross-Origin Resource Sharing) Errors in Frontend Console
- **Symptom:** `Access to fetch at 'http://localhost:8000' from origin 'http://localhost:8080' has been blocked by CORS policy`.
- **Solution:** In your `.env` or in `backend/app/config.py`, verify that `CORS_ORIGINS` includes your frontend port:
  ```env
  CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,http://localhost:3000,http://localhost
  ```

---

### Issue 3: MapLibre GL WebGL Context Lost or Canvas Not Rendering
- **Symptom:** Map displays as a blank grey canvas with a WebGL warning in Developer Tools.
- **Solution:**
  1. Verify browser hardware acceleration is enabled (`chrome://settings/system`).
  2. MapLibre automatically falls back to software rendering if WebGL 2.0 is disabled.
  3. Ensure container element `#map` has explicit dimensions in CSS: `width: 100vw; height: 100vh; position: absolute;`.

---

### Issue 4: Docker Compose Port Conflict (`port is already allocated`)
- **Symptom:** `Bind for 0.0.0.0:5432 failed: port is already allocated`.
- **Cause:** A local PostgreSQL or Redis instance is already running on host port 5432 or 6379.
- **Solution:** Override ports in `.env`:
  ```env
  POSTGRES_PORT=5433
  REDIS_PORT=6380
  ```

---

### Issue 5: Celery Worker Fails to Connect to Redis
- **Symptom:** `kombu.exceptions.OperationalError: [Errno 111] Connection refused`.
- **Solution:** Verify Redis container is running:
  ```bash
  docker ps -f name=bhusynch-redis
  ```
  Ensure the password in `REDIS_URL` matches `REDIS_PASSWORD` in `.env`.

---

## 6. Quick Reference Command Matrix

| Task | PowerShell (Windows) | Bash (Linux / macOS / Docker) |
| :--- | :--- | :--- |
| **Activate Virtualenv** | `.\backend\venv\Scripts\Activate.ps1` | `source backend/venv/bin/activate` |
| **Install Dev Packages**| `pip install -r backend/requirements-windows.txt` | `pip install -r backend/requirements.txt` |
| **Run Backend API** | `uvicorn app.main:app --reload --port 8000` | `uvicorn app.main:app --reload --port 8000` |
| **Run Celery Worker** | `celery -A app.workers.celery_app worker -l info -P solo` | `celery -A app.workers.celery_app worker -l info` |
| **Serve Frontend** | `cd frontend; python -m http.server 8080` | `cd frontend && python3 -m http.server 8080` |
| **Start Docker Stack** | `docker compose -f deployment/docker-compose.yml up -d` | `docker compose -f deployment/docker-compose.yml up -d` |
| **Stop Docker Stack** | `docker compose -f deployment/docker-compose.yml down` | `docker compose -f deployment/docker-compose.yml down` |
| **View Live API Logs** | `docker logs -f bhusynch-api` | `docker logs -f bhusynch-api` |
| **Open Postgres Shell**| `docker exec -it bhusynch-postgres psql -U bhusynch -d bhusynch_cadastral` | `docker exec -it bhusynch-postgres psql -U bhusynch -d bhusynch_cadastral` |
| **Run Test Suite** | `pytest -v` | `pytest -v` |
| **Deploy to K8s** | `kubectl apply -f deployment/k8s/` | `kubectl apply -f deployment/k8s/` |
