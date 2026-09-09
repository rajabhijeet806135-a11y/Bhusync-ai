# BhuSynch AI — Subsystem Pipeline Guide

> Detailed documentation of all 5 GeoAI subsystem pipelines

---

## Table of Contents

1. [Subsystem 1: Automated Geodesy & Deep Feature Co-Registration](#subsystem-1)
2. [Subsystem 2: Multilingual Document AI & ULPIN Generation](#subsystem-2)
3. [Subsystem 3: GeoAI Edge Conflation & Graph Neural Optimization](#subsystem-3)
4. [Subsystem 4: Three-Truths Conflict Arbitration & Covariance Engine](#subsystem-4)
5. [Subsystem 5: Distributed Topology & Cryptographic Provenance](#subsystem-5)

---

## Subsystem 1: Automated Geodesy & Deep Feature Co-Registration {#subsystem-1}

### Pipeline Flow

```
[Legacy Scanned Cloth Map (Sajra)] ──┐
                                     ├──▶ [SuperPoint] ──▶ [LightGlue] ──▶ [RANSAC GCP Set] ──┐
[5cm SoI Drone ORI + CORS Network] ──┘                                                         │
                                                                                               ▼
[WGS84 / EPSG:7755 GeoTIFF] ◀── [CORS Least-Squares] ◀── [TPS Warp] ◀── [Helmert 7-Param] ───┘
```

### Components

#### 1.1 Datum Shift (Kalianpur 1830 → WGS84 / EPSG:7755)

**File:** `backend/app/geodesy/datum_shift.py`

Implements the 7-parameter Bursa-Wolf formula for transforming coordinates from the legacy Kalianpur 1830 / Everest ellipsoid system to WGS84/EPSG:7755 (Indian National Grid).

**Formula:**
```
[X_WGS84]   [ΔX]            [1    -Rz   Ry ] [X_Everest]
[Y_WGS84] = [ΔY] + (1+s×1e-6)[Rz    1   -Rx] [Y_Everest]
[Z_WGS84]   [ΔZ]            [-Ry   Rx    1 ] [Z_Everest]
```

**Everest → WGS84 Parameters:**
| Parameter | Value |
|-----------|-------|
| ΔX | +295.0 m |
| ΔY | +736.0 m |
| ΔZ | +257.0 m |
| Rx | 0.0 arc-sec |
| Ry | 0.0 arc-sec |
| Rz | 0.0 arc-sec |
| s | 0.0 ppm |

Includes methods for:
- Geodetic (lat/lon/h) ↔ Cartesian (X/Y/Z) conversion
- Forward and inverse datum transformations
- Batch coordinate transformation

#### 1.2 SuperPoint Keypoint Detector

**File:** `backend/app/geoai/superpoint.py`

Computes dense interest point locations and descriptors on both historical scanned cloth maps and modern 5cm Drone Orthoimagery (ORI). Detects corner-like features robust to temporal and stylistic differences.

**Input:** Grayscale image tensor
**Output:** Keypoint coordinates (N×2) + 256-dim descriptors (N×256)

#### 1.3 LightGlue Cross-Attention Sparse Matcher

**File:** `backend/app/geoai/lightglue.py`

Performs cross-attention sparse matching between SuperPoint descriptors from the legacy and modern images. Uses learned attention-based pruning to robustly filter stylistic differences (ink-on-cloth vs. digital orthophoto).

**Input:** Two sets of keypoints + descriptors
**Output:** Matched pairs + confidence scores + filtered GCP set

#### 1.4 Helmert 7-Parameter Transformation

**File:** `backend/app/geodesy/helmert.py`

Applies a 7-parameter similarity transformation (3 translations, 3 rotations, 1 scale) computed from the matched GCPs.

#### 1.5 Thin-Plate Spline (TPS) Elastic Warp

**File:** `backend/app/geodesy/thin_plate_spline.py`

Corrects non-linear elastic deformation in scanned cloth maps (paper shrinkage, folding, scanning distortion). Minimizes bending energy while fitting control points.

**Energy Functional:**
```
E_TPS(f) = Σ||yi - f(xi)||² + λ∬(f_xx² + 2f_xy² + f_yy²) dx dy
```

The smoothing parameter λ controls the trade-off between interpolation fidelity and smoothness.

#### 1.6 CORS Constrained Least-Squares Adjustment

**File:** `backend/app/geodesy/cors_adjustment.py`

Final precision adjustment using Survey of India CORS (Continuously Operating Reference Stations) as fixed constraints. Computes optimal adjusted coordinates with RMSE quality metrics.

**Formula:**
```
x̂ = (AᵀPA)⁻¹AᵀPL,   RMSE = √(Σvi²/(n-m))
```

### Celery Task

**File:** `backend/app/workers/geodesy_tasks.py`

The full pipeline is executed as an async Celery chain:
1. `task_detect_keypoints` — SuperPoint detection on both images
2. `task_match_keypoints` — LightGlue matching
3. `task_helmert_transform` — Initial Helmert shift
4. `task_tps_warp` — Elastic deformation correction
5. `task_cors_adjust` — Final CORS adjustment

---

## Subsystem 2: Multilingual Document AI & ULPIN Generation {#subsystem-2}

### Pipeline Flow

```
[Scanned RoR/Jamabandi] ──▶ [LayoutLMv3] ──▶ [TrOCR Indic] ──▶ [Sarvam-1 LLM] ──▶ [Entity Tuples] ──▶ [ULPIN Encoder]
```

### Components

#### 2.1 LayoutLMv3 Table Segmenter

**File:** `backend/app/geoai/layout_lmv3.py`

Localizes table boundaries, column headers, and administrative seals in scanned Revenue Records (RoR), Jamabandi, Pahani, and Khatauni documents.

**Input:** Document image (scanned RoR page)
**Output:** Table regions, column headers, cell boundaries with semantic labels

#### 2.2 TrOCR Indic Script Recognition

**File:** `backend/app/geoai/trocr_indic.py`

Transformer-based OCR specifically trained for 22+ Indic scripts. Recognizes text in:
- Hindi (Devanagari), Marathi, Nepali
- Telugu, Tamil, Kannada, Malayalam
- Bengali, Odia, Assamese, Gujarati
- Punjabi (Gurmukhi), Urdu (Nastaliq)
- And more regional scripts

**Input:** Cropped text region image
**Output:** Recognized text string + per-character confidence

#### 2.3 Sarvam-1 Indic LLM

**File:** `backend/app/geoai/sarvam_llm.py`

Large Language Model specialized for Indian languages. Performs:
- **Ownership share parsing:** Interprets complex fractional ownership expressions
- **Area unit standardization:** Converts vernacular units to metric m²
  - Bigha (Bihar) → m²
  - Gunta (Karnataka) → m²
  - Katha (UP) → m²
  - Biswa (Rajasthan) → m²
- **Name normalization:** Handles transliteration variants across scripts

#### 2.4 Canonical Identity Vector

For cross-script name matching:
```
E_name = [E_phonetic, E_script, E_translit, E_context]
S_name = w₁·S_edit + w₂·S_phonetic + w₃·S_translit + w₄·S_context
```

#### 2.5 ULPIN (Bhu-Aadhaar) Generator

**File:** `backend/app/services/ulpin_service.py`

Generates 14-character Unique Land Parcel Identification Number per DoLR specification.

**Centroid Computation:**
```
Centroid(φc, λc) = (1/A ∮C x·dA, 1/A ∮C y·dA)
```

**Encoding:**
```
ULPIN = E_DoLR(φc, λc, Area_sqm, State_Code)
```

Format: `SS-DD-VVV-NNNN-CC` (State-District-Village-Serial-Check)

### Celery Task

**File:** `backend/app/workers/document_ai_tasks.py`

Pipeline: LayoutLMv3 → TrOCR → Sarvam-1 → Entity extraction → ULPIN assignment

---

## Subsystem 3: GeoAI Edge Conflation & Graph Neural Optimization {#subsystem-3}

### Pipeline Flow

```
[6-Channel Tensor: RGB + DSM + DTM + nDSM] ──▶ [SAM-Geo ViT-H] ──▶ [Douglas-Peucker] ──┐
                                                                                          ├──▶ [GIN Fréchet]
[Legacy Vector Khasra Polygons]             ──────────────────────────────────────────────┘
```

### Components

#### 3.1 SAM-Geo ViT-H Boundary Extraction

**File:** `backend/app/geoai/sam_geo.py`

Segment Anything Model (SAM) adapted for geospatial imagery. Uses 6-channel input:
1. Red, Green, Blue (RGB orthophoto)
2. Digital Surface Model (DSM)
3. Digital Terrain Model (DTM)
4. Normalized DSM (nDSM = DSM - DTM)

**Height Gradient Filter:**
```
∇nDSM = ∇(DSM - DTM) > 0.5m
```
Isolates compound walls and rooflines from ground shadows.

**Output:** Polygon masks of detected parcel boundaries

#### 3.2 Douglas-Peucker + Angle Regularizer

**File:** `backend/app/conflation/douglas_peucker.py`

Simplifies extracted boundaries while preserving cadastral-relevant angles (90° corners typical of surveyed parcels). The angle regularizer snaps near-orthogonal edges.

#### 3.3 GIN/GNN Fréchet Graph Matching

**File:** `backend/app/geoai/graph_neural.py` + `backend/app/conflation/frechet_matching.py`

Graph Isomorphism Network performs edge-level conflation between:
- **SAM-extracted boundaries** (physical truth)
- **Legacy khasra polygons** (legal truth)

**Fréchet Elastic Graph Optimization:**
```
min_d Σ D_Frechet(E_L,i, E_P,match) + γ Σ ||(pi+di-pj-dj) - (pi-pj)||²
```

#### 3.4 Hierarchical Block-Level ICP

**File:** `backend/app/conflation/icp_adjustment.py`

Iterative Closest Point (ICP) algorithm applied at block level to reduce systematic displacement. Achieves Suwardhi benchmark: 0.80m → 0.40-0.50m across block clusters.

### Celery Task

**File:** `backend/app/workers/conflation_tasks.py`

Pipeline: SAM-Geo → Douglas-Peucker → GIN Fréchet → Block ICP

---

## Subsystem 4: Three-Truths Conflict Arbitration & Covariance Engine {#subsystem-4}

### Decision Framework

```
              ┌────────────────────────────────┐
              │   Three-Truths Decision Core   │
              │ TL: Legal  TP: Physical  TA: Admin│
              └───────────────┬────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
    CASE A: Area         CASE B: RoW          CASE C: 3D
    ΔA > 2%              Encroachment         High-Rise
    Tolerance            Gair Mumkin          LADM
```

### Conflict Cases

#### Case A: Area Mismatch (ΔA > 2% Tolerance)

Detected when `|legal_area_sqm - observed_area_sqm| / legal_area_sqm > 0.02`.

Triggers revenue officer review for possible encroachment or survey error.

#### Case B: Public Right-of-Way (RoW) / Gair Mumkin Intrusion

Detected when SAM-extracted physical boundaries overlap with designated public areas (roads, canals, commons marked as "Gair Mumkin" in revenue records).

#### Case C: 3D High-Rise Multi-Storey LADM

Detected when nDSM analysis reveals multi-storey structures requiring Land Administration Domain Model (LADM) 3D parcellation.

### Vertex Error Covariance Ellipses

For each vertex of a harmonized parcel, the system computes error covariance:

```
Σ = (Σ wₛ Aₛᵀ Aₛ)⁻¹
```

Where `wₛ` are source weights (survey accuracy, drone GSD, historical map scale).

The ellipse parameters (semi-major, semi-minor, orientation) are stored in `parcel_vertices` and visualized as confidence ellipses on the Web-GIS frontend.

### Celery Task

**File:** `backend/app/workers/arbitration_tasks.py`

Handles Cases A, B, and C with automated conflict detection and severity classification.

---

## Subsystem 5: Distributed Topology & Cryptographic Provenance {#subsystem-5}

### Components

#### 5.1 Apache Sedona Topology Cleaning

Distributed spatial processing via Apache Sedona (Spark):
- **`ST_SnapToGrid(geom, 0.05)`** — Snapping to 5cm drone resolution
- **Constrained Delaunay Triangulation (CDT)** — Bridges micro-gaps without generating unallocated sliver polygons
- **Gap/overlap detection and repair** — Ensures topological consistency

#### 5.2 Siamese ChangeFormer

**File:** `backend/app/geoai/changeformer.py`

Bitemporal change detection using Siamese transformer architecture with differential DSM:

```
ΔC = σ(W · [||F_T1 - F_T2|| ∥ ΔDSM] + b)
```

**Decision Rule:**
- `ΔC = 1, ΔDSM > 2.5m` → **Unauthorized New Construction / Floor Addition**

Used for continuous monitoring of encroachment and unauthorized construction.

#### 5.3 Immutable Merkle Tree Provenance

**File:** `backend/app/provenance/merkle_tree.py`

SHA3-256 hash chain ensures tamper-proof audit trail:

```
H_k = SHA3-256(ULPIN ∥ Timestamp ∥ Officer_ID ∥ Geom_WKB ∥ H_{k-1})
```

Every modification to a parcel record creates a new entry in `cadastral_audit_ledger` with:
- Hash of previous entry (chain linkage)
- Current state hash
- Digital Signature Certificate (DSC) per IT Act 2000

#### 5.4 Digital Signature Certificates (DSC)

**File:** `backend/app/provenance/dsc_signer.py`

Implements signing and verification using PKCS#1 v1.5 with SHA-256, compliant with Section 3 of the Indian Information Technology Act, 2000.

### Celery Task

**File:** `backend/app/workers/topology_tasks.py`

Pipeline: Sedona topology repair → ChangeFormer detection → Merkle audit entry → DSC signing

---

## Model Registry

**File:** `backend/app/geoai/model_registry.py`

All AI/ML models are managed through a singleton registry with:
- **Lazy loading** — Models loaded on first use
- **TensorRT / ONNX Runtime optimization** — For production inference
- **GPU memory management** — Automatic device placement
- **Model versioning** — Track model weights and configurations

### Registered Models

| Model Key | Class | Input | Output |
|-----------|-------|-------|--------|
| `sam_geo` | `SAMGeoModel` | 6-ch tensor | Polygon masks |
| `superpoint` | `SuperPointModel` | Grayscale image | Keypoints + descriptors |
| `lightglue` | `LightGlueModel` | 2× keypoint sets | Matched pairs |
| `layout_lmv3` | `LayoutLMv3Model` | Document image | Table regions |
| `trocr_indic` | `TrOCRIndicModel` | Text region image | Recognized text |
| `sarvam_llm` | `SarvamLLMModel` | Text prompt | Parsed entities |
| `changeformer` | `ChangeFormerModel` | Bitemporal images | Change mask |
| `graph_neural` | `GraphNeuralModel` | Graph structure | Edge assignments |
