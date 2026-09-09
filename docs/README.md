# BhuSynch AI — National Urban Cadastral Intelligence Mesh

> **Problem Statement ID:** SIH 26013 — *Automated Integration and Intelligent Harmonization of Multi-source Geospatial Data for Urban Land Record Management*

---

## Overview

**BhuSynch AI** is a full-stack geospatial intelligence platform that automates the harmonization of multi-source cadastral data for Indian urban land record management. The system combines:

- **Computer Vision Foundation Models** (SAM-Geo, SuperPoint, LightGlue, ChangeFormer)
- **Graph Neural Conflation** (GIN/GNN Fréchet elastic optimization)
- **Multilingual Document AI** (LayoutLMv3, TrOCR Indic, Sarvam-1 LLM)
- **Cryptographic Provenance** (SHA3-256 Merkle Tree, DSC signing)

### Governance Standards
- **NAKSHA** (DoLR / MoRD)
- **Survey of India CORS**
- **DILRMP**
- **ULPIN (Bhu-Aadhaar)** — 14-character unique land parcel identification

---

## System Architecture

```
CLIENT TIER                    API GATEWAY              ASYNC ORCHESTRATION
┌──────────────┐              ┌──────────┐             ┌──────────────────┐
│ 3D Web-GIS   │──┐           │ Kong +   │             │ FastAPI → Celery │
│ Console      │  │           │ Keycloak │             │ → Redis/RabbitMQ │
├──────────────┤  ├──────────▶│ OIDC     │────────────▶│                  │
│ Mobile PWA   │  │           │ RBAC/ABAC│             │ Job State Track  │
├──────────────┤  │           └──────────┘             └────────┬─────────┘
│ Revenue      │──┘                                            │
│ Adjudication │                                    ┌──────────┼──────────┐
└──────────────┘                                    ▼          ▼          ▼
                                               Geodesy    GeoAI Ray   Document AI
                                               Workers    Cluster     Workers
                                                    │          │          │
                                                    └──────────┼──────────┘
                                                               ▼
                                               ┌──────────────────────────┐
                                               │ PostgreSQL + PostGIS     │
                                               │ Apache Sedona (Spark)    │
                                               │ MinIO S3 Object Storage  │
                                               └──────────────────────────┘
```

---

## Project Structure

```
website/
├── backend/                    # FastAPI + Celery Backend
│   ├── app/
│   │   ├── api/                # Route handlers (OGC + REST)
│   │   ├── models/             # SQLAlchemy ORM Models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic layer
│   │   ├── workers/            # Celery async task definitions
│   │   ├── geoai/              # AI/ML model interfaces
│   │   ├── geodesy/            # Geodesy computation modules
│   │   ├── conflation/         # Conflation algorithms
│   │   ├── provenance/         # Cryptographic audit
│   │   └── utils/              # Shared utilities
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Test suite
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pyproject.toml
│
├── frontend/                   # 3D Web-GIS Console + Revenue Portal
│   ├── index.html              # Main 3D console
│   ├── adjudication.html       # Revenue Adjudication Portal
│   ├── css/                    # Stylesheets
│   └── js/                     # JavaScript modules
│
├── mobile-pwa/                 # Mobile Ground-Truthing PWA
│   ├── index.html
│   ├── manifest.json
│   ├── sw.js
│   ├── css/
│   └── js/
│
├── deployment/                 # Docker & Kubernetes
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   ├── Dockerfile.frontend
│   ├── k8s/                    # Kubernetes manifests
│   └── nginx/                  # Nginx config
│
├── sql/                        # Raw SQL schemas
│   └── init.sql
│
└── docs/                       # Documentation
    ├── README.md
    ├── API_REFERENCE.md
    ├── SUBSYSTEM_GUIDE.md
    └── DEPLOYMENT_GUIDE.md
```

---

## 5 Core Subsystems

| # | Subsystem | Description | Key Technologies |
|---|-----------|-------------|------------------|
| 1 | **Automated Geodesy & Deep Feature Co-Registration** | Datum shift, auto-GCP, elastic warp | SuperPoint, LightGlue, Helmert, TPS |
| 2 | **Multilingual Document AI & ULPIN Generation** | OCR, entity extraction, parcel ID | LayoutLMv3, TrOCR, Sarvam-1, ULPIN |
| 3 | **GeoAI Edge Conflation & Graph Neural Optimization** | Boundary extraction, vector conflation | SAM-Geo, Douglas-Peucker, GIN/GNN |
| 4 | **Three-Truths Conflict Arbitration & Covariance Engine** | Legal/Physical/Admin conflict detection | Covariance ellipses, dossier generation |
| 5 | **Distributed Topology & Cryptographic Provenance** | Topology cleaning, tamper-proof audit | Sedona CDT, ChangeFormer, Merkle tree |

---

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 16 with PostGIS 3.4
- Redis (for Celery broker)
- Docker & Docker Compose (for full stack)

### Development Setup

1. **Clone and install backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up environment variables** (see `backend/app/config.py` for all settings):
   ```bash
   export DATABASE_URL="postgresql+asyncpg://bhusynch:password@localhost:5432/bhusynch_ai"
   export REDIS_URL="redis://localhost:6379/0"
   export MINIO_ENDPOINT="localhost:9000"
   ```

3. **Initialize database:**
   ```bash
   psql -U postgres -f sql/init.sql
   # Or use Alembic:
   cd backend && alembic upgrade head
   ```

4. **Run the API server:**
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Start Celery workers:**
   ```bash
   cd backend
   celery -A app.workers.celery_app worker --loglevel=info
   ```

6. **Open the frontend:**
   Open `frontend/index.html` in a browser, or serve via nginx.

### Docker Compose (Full Stack)

```bash
cd deployment
docker-compose up -d
```

This starts: FastAPI, Celery workers, PostgreSQL+PostGIS, Redis, MinIO, Martin tile server, Keycloak, Kong gateway.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend API** | FastAPI, Uvicorn, Pydantic v2 |
| **Async Workers** | Celery, Redis/RabbitMQ |
| **Database** | PostgreSQL 16, PostGIS 3.4, GeoAlchemy2 |
| **Spatial Compute** | Apache Sedona (Spark) |
| **Object Storage** | MinIO (S3 API) |
| **AI/ML Inference** | PyTorch, TensorRT, ONNX Runtime, Ray |
| **Tile Server** | Martin (MVT Vector Tiles) |
| **Frontend** | MapLibre GL JS, Deck.gl |
| **Auth** | Keycloak OIDC (OAuth 2.0 / JWT) |
| **API Gateway** | Kong |
| **Container** | Docker, Kubernetes |
| **Cloud** | NIC MeghRaj Sovereign Cloud |

---

## Documentation

- [Complete Beginner's Master Guide](./COMPLETE_BEGINNERS_GUIDE.md) — Step-by-step concepts, architecture, and user guide
- [Prototype vs. Production Guide](./PRODUCTION_VS_PROTOTYPE.md) — Differences, requirements, and enterprise rollout guide
- [System Readiness Report](./SYSTEM_READINESS_REPORT.md) — Comprehensive readiness audit & test pass breakdown
- [API Reference](./API_REFERENCE.md) — Full OGC + REST API documentation
- [Subsystem Guide](./SUBSYSTEM_GUIDE.md) — All 5 subsystem pipeline documentation
- [Deployment Guide](./DEPLOYMENT_GUIDE.md) — Docker & K8s deployment instructions
- [Architecture Plan](../PLAN_ALPHA_SYSTEM_ARCHITECTURE.md) — Complete system architecture specification

---

## License

This project is developed for the Smart India Hackathon 2026 (SIH 26013). All rights reserved.
