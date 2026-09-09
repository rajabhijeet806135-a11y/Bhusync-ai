# Plan Alpha: Complete System Architecture Specification
## National Urban Cadastral Intelligence Mesh (BhuSynch AI)

**Problem Statement ID:** SIH 26013 — *Automated Integration and Intelligent Harmonization of Multi-source Geospatial Data for Urban Land Record Management*  
**Architecture Paradigm:** Computer Vision Foundation Models + Graph Neural Conflation (Deep GeoAI First)  
**Governance Standard:** NAKSHA (DoLR / MoRD), Survey of India CORS, DILRMP, ULPIN (Bhu-Aadhaar)

---

# 1. End-to-End System Topology

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           CLIENT PRESENTATION TIER                                     │
│  ┌───────────────────────────────┐   ┌───────────────────────────────┐   ┌───────────────────────────┐ │
│  │ 3D Web-GIS Console            │   │ Mobile Ground-Truthing PWA    │   │ Revenue Adjudication Port.│ │
│  │ (MapLibre GL JS + Deck.gl MVT)│   │ (Encrypted OGC GeoPackage)    │   │ (Statutory Dossier & RoR) │ │
│  └──────────────┬────────────────┘   └───────────────┬───────────────┘   └─────────────┬─────────────┘ │
└─────────────────┼────────────────────────────────────┼─────────────────────────────────┼───────────────┘
                  │                                    │                                 │
                  ▼                                    ▼                                 ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   API GATEWAY & SECURITY INGRESS (KONG)                                │
│         • Keycloak OIDC (OAuth 2.0 / JWT)   • Rate Limiting & SSL Termination   • Role-Based RBAC/ABAC │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     ASYNCHRONOUS ORCHESTRATION LAYER                                   │
│  ┌──────────────────────────────┐     ┌───────────────────────────────┐     ┌────────────────────────┐ │
│  │ FastAPI REST Endpoints       │────▶│ Celery Task Producer          │────▶│ Redis / RabbitMQ Queue │ │
│  │ (OGC Features/Processes/Tiles│     │ (Job State Tracking & Event)  │     │ (Distributed Worker MS)│ │
│  └──────────────────────────────┘     └───────────────────────────────┘     └───────────┬────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────┼──────────────┘
                                                                                          │
        ┌─────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────┐
        │                                                                                 │                                        │
        ▼                                                                                 ▼                                        ▼
┌────────────────────────────────────────┐     ┌────────────────────────────────────────┐     ┌────────────────────────────────────────┐
│       INGESTION & GEODESY WORKERS      │     │      RAY GeoAI INFERENCE CLUSTER       │     │     DOCUMENT AI & SEMANTIC WORKERS     │
│ • GDAL/Rasterio COG & LAS converter    │     │ • SAM-Geo (ViT-H) + Mask2Former Pool   │     │ • CRAFT / LayoutLMv3 Table Segmenter   │
│ • SuperPoint + LightGlue Auto-GCP Match│     │ • Graph Neural Conflation (GIN / GNN)  │     │ • IndicOCR (TrOCR) + Sarvam-1 Indic-LLM│
│ • 7-Param Helmert + TPS Elastic Warp   │     │ • Siamese ChangeFormer (Bitemporal)    │     │ • Canonical Name Vectors & Linkage     │
│ • Survey of India CORS Least Squares   │     │ • TensorRT / ONNX Runtime Optimization │     │ • Centroid 14-Character ULPIN Engine   │
└──────────────────┬─────────────────────┘     └──────────────────┬─────────────────────┘     └──────────────────┬─────────────────────┘
                   │                                              │                                              │
                   └──────────────────────────────────────────────┼──────────────────────────────────────────────┘
                                                                  │
                                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                DISTRIBUTED SPATIAL STORAGE & COMPUTE CORE                                        │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐   ┌─────────────────────────────────────────────────┐ │
│  │ PostgreSQL 16 + PostGIS 3.4     │   │ Apache Sedona (Spark Engine)    │   │ MinIO Object Storage (S3 API)                   │ │
│  │ (Authoritative Parcels & DB)    │   │ (Distributed Topology Clean CDT)│   │ (Cloud Optimized GeoTIFFs, LAS/LAZ Point Cloud) │ │
│  └────────────────┬────────────────┘   └────────────────┬────────────────┘   └────────────────────────┬────────────────────────┘ │
└───────────────────┼─────────────────────────────────────┼─────────────────────────────────────────────┼──────────────────────────┘
                    │                                     │                                             │
                    └─────────────────────────────────────┼─────────────────────────────────────────────┘
                                                          │
                                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                            EVIDENCE ARBITRATION & TAMPER-PROOF AUDIT CORE                                        │
│  • The Three-Truths Matrix (Legal TL vs Physical TP vs Administrative TA)    • Vertex Covariance Error Ellipses Σ = (Σ w A^T A)^(-1)│
│  • SHA3-256 Merkle Tree Immutable Provenance Ledger                         • Digital Signature Certificates (DSC - IT Act 2000)│
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# 2. Granular Subsystem Pipelines

## 2.1 Subsystem 1: Automated Geodesy & Deep Feature Co-Registration

```
[Legacy Scanned Cloth Map (Sajra)] ──┐
                                     ├──> [SuperPoint Detector] ──> [LightGlue Matcher] ──> [RANSAC GCP Set] ──┐
[5cm SoI Drone ORI + CORS Network] ──┘                                                                         │
                                                                                                               ▼
[WGS84 / EPSG:7755 GeoTIFF] <── [CORS Least-Squares] <── [Thin-Plate Spline Warp] <── [Helmert 7-Param Shift] ─┘
```

1. **Datum Shift Formulation (Kalianpur 1830 to WGS84 / EPSG:7755):**
   $$\begin{bmatrix} X_{\text{WGS84}} \\ Y_{\text{WGS84}} \\ Z_{\text{WGS84}} \end{bmatrix} = \begin{bmatrix} \Delta X \\ \Delta Y \\ \Delta Z \end{bmatrix} + (1 + s \times 10^{-6}) \begin{bmatrix} 1 & -R_z & R_y \\ R_z & 1 & -R_x \\ -R_y & R_x & 1 \end{bmatrix} \begin{bmatrix} X_{\text{Everest}} \\ Y_{\text{Everest}} \\ Z_{\text{Everest}} \end{bmatrix}$$
2. **Automated Deep Keypoint Matching (Zero Manual GCP Clicking):**
   - **SuperPoint:** Computes dense interest point locations and descriptors on historical scanned cloth maps and modern 5cm Drone ORI.
   - **LightGlue:** Performs cross-attention sparse matching, robustly filtering stylistic and temporal differences.
3. **Thin-Plate Spline (TPS) Elastic Deformation Correction:**
   $$E_{\text{TPS}}(f) = \sum_{i=1}^N \|y_i - f(x_i)\|^2 + \lambda \iint_{\mathbb{R}^2} \left( \left(\frac{\partial^2 f}{\partial x_1^2}\right)^2 + 2\left(\frac{\partial^2 f}{\partial x_1 \partial x_2}\right)^2 + \left(\frac{\partial^2 f}{\partial x_2^2}\right)^2 \right) dx_1 dx_2$$
4. **CORS Constrained Least Squares Adjustment:**
   $$\hat{x} = (A^T P A)^{-1} A^T P L, \quad \text{RMSE} = \sqrt{\frac{\sum v_i^2}{n-m}}$$

---

## 2.2 Subsystem 2: Multilingual Document AI & ULPIN Generation

```
[Scanned RoR/Jamabandi] ──> [LayoutLMv3] ──> [TrOCR Indic] ──> [Sarvam-1 LLM] ──> [Entity Tuples] ──> [ULPIN Encoder]
```

1. **Multi-Task Extraction:**
   - **LayoutLMv3:** Localizes table boundaries, column headers, and administrative seals.
   - **TrOCR:** Script-specific transformer recognition for 22+ Indic scripts (Hindi, Marathi, Telugu, Tamil, Bengali, Kannada, etc.).
   - **Sarvam-1 / Indic-LLM:** Parses ownership shares and standardizes vernacular area units (*Bigha, Gunta, Katha, Biswa*) into metric $\text{m}^2$.
2. **Canonical Identity Vector for Name Resolution:**
   $$E_{\text{name}} = [E_{\text{phonetic}}, E_{\text{script}}, E_{\text{translit}}, E_{\text{context}}]$$
   $$S_{\text{name}} = w_1 S_{\text{edit}} + w_2 S_{\text{phonetic}} + w_3 S_{\text{translit}} + w_4 S_{\text{context}}$$
3. **14-Character ULPIN (Bhu-Aadhaar) Centroid Encoding:**
   $$\text{Centroid } (\phi_c, \lambda_c) = \left( \frac{1}{A} \oint_C x \cdot \mathrm{d}A, \; \frac{1}{A} \oint_C y \cdot \mathrm{d}A \right)$$
   $$\text{ULPIN} = \mathcal{E}_{\text{DoLR}}(\phi_c, \lambda_c, \text{Area}_{\text{sqm}}, \text{State\_Code})$$

---

## 2.3 Subsystem 3: GeoAI Edge Conflation & Graph Neural Optimization

```
[6-Channel Tensor: RGB + DSM + DTM + nDSM] ──> [SAM-Geo ViT-H] ──> [Douglas-Peucker + Angle Regularizer] ──┐
                                                                                                           ├──> [GIN Fréchet Matching]
[Legacy Vector Khasra Polygons]             ───────────────────────────────────────────────────────────────┘
```

1. **Height Gradient Boundary Extraction:**
   - Evaluates $\nabla n\text{DSM} = \nabla(\text{DSM} - \text{DTM}) > 0.5\text{m}$ to isolate compound walls and rooflines from ground shadows.
2. **Deformable Vector Conflation (Fréchet Elastic Graph Optimization):**
   $$\min_{\mathbf{d}} \sum_{i \in V_L} \mathcal{D}_{\text{Frechet}}(E_{L,i}, E_{P,\text{match}}) + \gamma \sum_{(i,j) \in E_L} \left\| (\mathbf{p}_i + \mathbf{d}_i - \mathbf{p}_j - \mathbf{d}_j) - (\mathbf{p}_i - \mathbf{p}_j) \right\|^2$$
3. **Hierarchical Block-Level ICP Adjustment (Suwardhi Benchmark):**
   - Automatically reduces boundary displacement from $0.80\text{m}$ down to $0.40\text{m} - 0.50\text{m}$ across block clusters.

---

## 2.4 Subsystem 4: Three-Truths Conflict Arbitration & Covariance Engine

```
                             ┌───────────────────────────────────────┐
                             │       Three-Truths Decision Core      │
                             │   (TL: Legal, TP: Physical, TA: Admin)│
                             └───────────────────┬───────────────────┘
                                                 │
            ┌────────────────────────────────────┼────────────────────────────────────┐
            ▼                                    ▼                                    ▼
┌────────────────────────┐           ┌────────────────────────┐           ┌────────────────────────┐
│ CASE A: Area Mismatch  │           │ CASE B: Public RoW /   │           │ CASE C: 3D High-Rise   │
│ ΔA > 2% Tolerance      │           │ Gair Mumkin Intrusion  │           │ Multi-Storey LADM      │
└───────────┬────────────┘           └───────────┬────────────┘           └───────────┬────────────┘
            │                                    │                                    │
            └────────────────────────────────────┼────────────────────────────────────┘
                                                 │
                                                 ▼
                             ┌───────────────────────────────────────┐
                             │ Vertex Error Covariance Ellipses (Σ)  │
                             │ Σ = (Σ w_s A_s^T A_s)^(-1)            │
                             └───────────────────┬───────────────────┘
                                                 │
                                                 ▼
                             ┌───────────────────────────────────────┐
                             │ Statutory Revenue Adjudication Dossier│
                             │ ("AI Proposes, Officer Disposes")     │
                             └───────────────────────────────────────┘
```

---

## 2.5 Subsystem 5: Distributed Topology & Cryptographic Provenance

1. **Apache Sedona (Spark) Topology Cleaning:**
   - `ST_SnapToGrid(geom, 0.05)` (Snapping to 5cm drone resolution).
   - Constrained Delaunay Triangulation (CDT) bridges micro-gaps without generating unallocated sliver polygons.
2. **Siamese ChangeFormer & Differential DSM Encroachment Detection:**
   $$\Delta C = \sigma\left( \mathbf{W} \cdot \left[ \|\mathbf{F}_{T1} - \mathbf{F}_{T2}\| \;\parallel\; \Delta\text{DSM} \right] + \mathbf{b} \right)$$
   - $\Delta C = 1, \Delta\text{DSM} > 2.5\text{m} \implies$ **Unauthorized New Construction / Floor Addition**.
3. **Immutable Merkle Tree Provenance:**
   $$H_k = \text{SHA3-256}(\text{ULPIN} \parallel \text{Timestamp} \parallel \text{Officer\_ID} \parallel \text{Geom}_{\text{WKB}} \parallel H_{k-1})$$
   - Digitally signed with authorized Digital Signature Certificates (DSC) under Section 3 of the Indian Information Technology Act, 2000.

---

# 3. Database Schema Design (PostgreSQL / PostGIS DDL)

```sql
-- Enable PostGIS & Vector Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Base Cadastral Parcels Table
CREATE TABLE cadastral_parcels (
    parcel_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ulpin VARCHAR(14) UNIQUE,
    state_code VARCHAR(2) NOT NULL,
    district_code VARCHAR(3) NOT NULL,
    village_code VARCHAR(6) NOT NULL,
    khasra_no VARCHAR(50) NOT NULL,
    khata_no VARCHAR(50),
    legal_area_sqm NUMERIC(12, 4) NOT NULL,
    observed_area_sqm NUMERIC(12, 4),
    status VARCHAR(30) DEFAULT 'PROVISIONAL', -- CANDIDATE, VERIFIED, ADJUDICATED
    geom GEOMETRY(Polygon, 7755) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_parcels_geom ON cadastral_parcels USING GIST(geom);

-- 2. Vertex Error Covariance Table
CREATE TABLE parcel_vertices (
    vertex_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parcel_id UUID REFERENCES cadastral_parcels(parcel_id) ON DELETE CASCADE,
    vertex_index INT NOT NULL,
    sigma_major_axis_m NUMERIC(6, 4) NOT NULL, -- Semi-major axis of error ellipse
    sigma_minor_axis_m NUMERIC(6, 4) NOT NULL, -- Semi-minor axis of error ellipse
    orientation_deg NUMERIC(5, 2) NOT NULL,
    confidence_score NUMERIC(4, 3) NOT NULL,
    geom GEOMETRY(Point, 7755) NOT NULL
);
CREATE INDEX idx_vertices_geom ON parcel_vertices USING GIST(geom);

-- 3. Legal RoR Ownership Registry
CREATE TABLE revenue_ownership_records (
    record_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parcel_id UUID REFERENCES cadastral_parcels(parcel_id),
    owner_name_vernacular TEXT NOT NULL,
    owner_name_english TEXT NOT NULL,
    father_spouse_name TEXT,
    share_fraction VARCHAR(20) DEFAULT '1/1',
    land_type VARCHAR(50), -- Khari, Bagayat, Gair Mumkin
    encumbrance_status TEXT,
    ocr_confidence NUMERIC(4, 3),
    raw_document_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Spatial Conflict Cases Table
CREATE TABLE spatial_conflicts (
    conflict_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parcel_id UUID REFERENCES cadastral_parcels(parcel_id),
    conflict_type VARCHAR(50) NOT NULL, -- AREA_DISCREPANCY, ROW_ENCROACHMENT, 3D_OVERLAP
    severity VARCHAR(20) NOT NULL, -- LOW, MEDIUM, CRITICAL
    discrepancy_area_sqm NUMERIC(10, 4),
    disputed_geometry GEOMETRY(Geometry, 7755) NOT NULL,
    evidence_payload JSONB NOT NULL,
    adjudication_status VARCHAR(30) DEFAULT 'PENDING_OFFICER_REVIEW',
    assigned_officer_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_conflicts_geom ON spatial_conflicts USING GIST(disputed_geometry);

-- 5. Immutable Merkle Audit Ledger
CREATE TABLE cadastral_audit_ledger (
    entry_id BIGSERIAL PRIMARY KEY,
    ulpin VARCHAR(14) NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- RECTIFICATION, MUTATION, ADJUDICATION
    officer_id VARCHAR(100) NOT NULL,
    prev_merkle_hash VARCHAR(64) NOT NULL,
    current_hash VARCHAR(64) NOT NULL,
    dsc_signature TEXT NOT NULL,
    payload_snapshot JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

# 4. Standard OGC & REST API Specifications

| Endpoint | Method | Standard Protocol | Purpose |
| :--- | :---: | :--- | :--- |
| `/ogc/features/collections/parcels/items` | `GET` | **OGC API – Features (Part 1 & 2)** | Query harmonized parcels with CRS filtering (`EPSG:7755`, `EPSG:4326`). |
| `/ogc/features/collections/parcels/items/{ulpin}` | `GET` | **OGC API – Features** | Retrieve individual parcel digital twin, error ellipses, and ownership records. |
| `/ogc/processes/georeference/execution` | `POST` | **OGC API – Processes (Async)** | Trigger automated SuperPoint + LightGlue + TPS warping job on uploaded *Sajra*. |
| `/ogc/processes/conflation/execution` | `POST` | **OGC API – Processes (Async)** | Execute SAM-Geo boundary segmentation and Fréchet graph conflation. |
| `/ogc/tiles/parcels/{z}/{x}/{y}.pbf` | `GET` | **OGC API – Tiles (MVT)** | Blazing-fast Mapbox Vector Tiles streaming to MapLibre GL frontend. |
| `/api/v1/adjudication/dossier/{ulpin}` | `POST` | **Custom REST (JSON/PDF)** | Generate legally certified statutory adjudication dossier with DSC signatures. |
| `/api/v1/audit/verify/{ulpin}` | `GET` | **Custom REST** | Returns full cryptographic Merkle hash chain for judicial non-repudiation. |

---

# 5. Production Deployment Topology (NIC MeghRaj Sizing)

```
┌────────────────────────────────────────────────────────────────────────┐
│             SOVEREIGN CLOUD DEPLOYMENT (NIC MeghRaj / K8s)             │
│                                                                        │
│  ┌───────────────────────┐   ┌──────────────────────────────────────┐  │
│  │ Ingress & API Tier    │   │ GeoAI Worker Pool (GPU Nodes)        │  │
│  │ • 3x Kong / NGINX     │   │ • 4x Nvidia A10G / L4 (24GB VRAM)    │  │
│  │ • 4x FastAPI Instances│   │ • PyTorch + TensorRT + Ray Core      │  │
│  │ • 2x Keycloak OIDC    │   │ • SAM-Geo, LightGlue, LayoutLMv3     │  │
│  └───────────────────────┘   └──────────────────────────────────────┘  │
│                                                                        │
│  ┌───────────────────────┐   ┌──────────────────────────────────────┐  │
│  │ Distributed Database  │   │ Storage & Tile Acceleration          │  │
│  │ • PostgreSQL Primary  │   │ • MinIO S3 (Distributed 4-Node COG)  │  │
│  │ • 2x PostGIS Read-Reps│   │ • Martin Tile Server (MVT Vector)    │  │
│  │ • Apache Sedona Spark │   │ • Redis Cluster (Celery Task Broker) │  │
│  └───────────────────────┘   └──────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```
