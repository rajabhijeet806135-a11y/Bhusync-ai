# BhuSynch AI — Deployment Guide

> **National Urban Cadastral Intelligence Mesh**
> Production & Development Deployment Reference

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Repository Structure](#2-repository-structure)
3. [Environment Configuration](#3-environment-configuration)
4. [Development Deployment (Docker Compose)](#4-development-deployment)
5. [Production Deployment (Docker Compose)](#5-production-deployment)
6. [Kubernetes Deployment (NIC MeghRaj / K8s)](#6-kubernetes-deployment)
7. [Service Reference](#7-service-reference)
8. [SSL & Ingress Configuration](#8-ssl--ingress-configuration)
9. [Database Initialization](#9-database-initialization)
10. [Storage & Object Store (MinIO)](#10-storage--object-store-minio)
11. [Monitoring & Health Checks](#11-monitoring--health-checks)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Prerequisites

### Required Software

| Component           | Minimum Version | Purpose                                |
| :------------------ | :-------------- | :------------------------------------- |
| Docker Engine       | 24.0+           | Container runtime                      |
| Docker Compose      | 2.20+           | Multi-container orchestration          |
| kubectl             | 1.28+           | Kubernetes cluster management          |
| Helm (optional)     | 3.12+           | K8s package management                 |
| Git                 | 2.40+           | Source control                         |

### Hardware Requirements

#### Development Environment

- **CPU:** 4 cores minimum
- **RAM:** 16 GB minimum
- **Disk:** 50 GB SSD

#### Production Environment (NIC MeghRaj Sizing)

| Tier                    | Specification                                              |
| :---------------------- | :--------------------------------------------------------- |
| **Ingress & API Tier**  | 3× Kong/NGINX instances, 4× FastAPI pods, 2× Keycloak OIDC |
| **GeoAI Worker Pool**   | 4× NVIDIA A10G / L4 (24 GB VRAM), PyTorch + TensorRT + Ray |
| **Distributed Database**| PostgreSQL 16 Primary + 2× PostGIS read replicas           |
| **Storage**             | MinIO S3 (4-node distributed COG), Martin Tile Server (MVT) |
| **Task Broker**         | Redis Cluster (Celery distributed worker micro-services)    |

---

## 2. Repository Structure

```
project-root/
├── backend/                    # FastAPI application & Celery workers
│   ├── app/
│   │   ├── main.py             # Application entrypoint
│   │   ├── api/                # OGC & REST API routers
│   │   ├── models/             # ML model interfaces (SAM-Geo, LightGlue, etc.)
│   │   ├── workers/            # Celery task pipelines (5 subsystems)
│   │   └── core/               # Config, security, database
│   ├── Dockerfile              # Backend container image
│   └── requirements.txt        # Python dependencies
├── frontend/                   # 3D Web-GIS Console (MapLibre GL + Deck.gl)
├── mobile-pwa/                 # Mobile Ground-Truthing PWA
├── deployment/
│   ├── docker-compose.yml      # Production multi-service compose
│   ├── docker-compose.dev.yml  # Development overrides (hot-reload, debug)
│   ├── Dockerfile.frontend     # NGINX-based frontend container
│   ├── nginx/
│   │   └── default.conf        # NGINX reverse proxy configuration
│   └── k8s/                    # Kubernetes manifests
│       ├── namespace.yaml
│       ├── postgres-statefulset.yaml
│       ├── redis-deployment.yaml
│       ├── minio-statefulset.yaml
│       ├── martin-deployment.yaml
│       ├── keycloak-deployment.yaml
│       ├── api-deployment.yaml
│       ├── worker-deployment.yaml
│       └── ingress.yaml
├── sql/
│   └── init.sql                # PostgreSQL/PostGIS schema initialization
└── docs/                       # Documentation
```

---

## 3. Environment Configuration

Create a `.env` file in the project root before deploying.

### Required Variables

```bash
# ─── PostgreSQL ───────────────────────────────
POSTGRES_USER=bhusynch
POSTGRES_PASSWORD=<strong-password>
POSTGRES_PORT=5432

# ─── Redis ────────────────────────────────────
REDIS_PASSWORD=<strong-password>
REDIS_PORT=6379

# ─── MinIO Object Storage ────────────────────
MINIO_ROOT_USER=bhusynch_minio
MINIO_ROOT_PASSWORD=<strong-password>
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001

# ─── Keycloak OIDC ───────────────────────────
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=<strong-password>
KEYCLOAK_PORT=8080

# ─── API ──────────────────────────────────────
API_PORT=8000
CORS_ORIGINS=https://bhusynch.gov.in,https://admin.bhusynch.gov.in

# ─── Frontend ─────────────────────────────────
FRONTEND_PORT=80

# ─── Martin Tile Server ──────────────────────
MARTIN_PORT=3000
```

> **IMPORTANT:** Variables marked with `?` in compose files (`${VAR:?message}`) are **mandatory** and will cause a startup failure if not set.

---

## 4. Development Deployment

### Quick Start

```bash
# 1. Clone the repository
git clone <repository-url> && cd <project-root>

# 2. Create development .env
cp .env.example .env
# Edit .env with dev-friendly passwords

# 3. Launch all services with dev overrides
docker compose -f deployment/docker-compose.yml \
               -f deployment/docker-compose.dev.yml up --build
```

### Development Features

The `docker-compose.dev.yml` overlay provides:

| Feature                | Description                                                    |
| :--------------------- | :------------------------------------------------------------- |
| **Hot Reload**         | FastAPI runs with `--reload`, code changes apply instantly      |
| **Debug Logging**      | All services set to `LOG_LEVEL=DEBUG`                          |
| **Volume Mounts**      | `./backend` and `./frontend` mounted for live editing           |
| **pgAdmin**            | Database GUI at `http://localhost:5050`                         |
| **Redis Commander**    | Cache inspection at `http://localhost:8081`                     |
| **Relaxed Auth**       | Redis runs without password, Keycloak uses `admin/admin`        |
| **Reduced Concurrency**| Celery worker uses `--concurrency=2` for lighter resource usage |

### Service URLs (Development)

| Service          | URL                           |
| :--------------- | :---------------------------- |
| Frontend         | `http://localhost`            |
| API Docs         | `http://localhost:8000/docs`  |
| pgAdmin          | `http://localhost:5050`       |
| Redis Commander  | `http://localhost:8081`       |
| MinIO Console    | `http://localhost:9001`       |
| Keycloak Admin   | `http://localhost:8080`       |
| Martin Tiles     | `http://localhost:3000`       |

---

## 5. Production Deployment

### Launch

```bash
# 1. Ensure .env is configured with strong production passwords
# 2. Build and start all services
docker compose -f deployment/docker-compose.yml up -d --build

# 3. Verify all services are healthy
docker compose -f deployment/docker-compose.yml ps
```

### Service Architecture

The production stack deploys 8 services:

```
┌─────────────────────────────────────────────────────────────────┐
│                    docker-compose.yml                            │
│                                                                 │
│  postgres (PostGIS 16-3.4)  ←──── sql/init.sql (schema)        │
│  redis (7-alpine)           ←──── Celery broker + cache         │
│  minio (S3 API)             ←──── COG/LAS/LAZ storage           │
│  martin (MapLibre MVT)      ←──── Vector tile serving           │
│  keycloak (OIDC 24.0)       ←──── JWT authentication            │
│  api (FastAPI)              ←──── OGC + REST endpoints          │
│  worker (Celery)            ←──── 5 subsystem task queues       │
│  frontend (NGINX)           ←──── 3D Web-GIS + PWA              │
└─────────────────────────────────────────────────────────────────┘
```

### Celery Queue Topology

The Celery worker subscribes to all 5 subsystem queues:

```
geodesy       → Subsystem 1: Automated Geodesy & Deep Feature Co-Registration
document_ai   → Subsystem 2: Multilingual Document AI & ULPIN Generation
geoai         → Subsystem 3: SAM-Geo Boundary Segmentation & Conflation
conflation    → Subsystem 4: Evidence Arbitration & Adjudication
topology      → Subsystem 5: Topology Cleaning & Authoritative Commit
```

### Persistent Volumes

| Volume          | Mount Target                           | Purpose                    |
| :-------------- | :------------------------------------- | :------------------------- |
| `postgres_data` | `/var/lib/postgresql/data`             | Cadastral database storage |
| `redis_data`    | `/data`                                | Task broker persistence    |
| `minio_data`    | `/data`                                | COG/LAS object storage     |
| `api_uploads`   | `/app/uploads`                         | Uploaded survey documents  |
| `api_temp`      | `/app/temp`                            | Temporary processing files |

---

## 6. Kubernetes Deployment

### Namespace Setup

```bash
# Apply the namespace and resource quotas
kubectl apply -f deployment/k8s/namespace.yaml
```

The namespace `bhusynch-system` is created with:
- **CPU Quota:** 32 cores total, 4 cores default per pod
- **Memory Quota:** 128 Gi total, 8 Gi default per pod
- **GPU Quota:** 4 NVIDIA GPUs
- Pod labels for NIC MeghRaj sovereign cloud governance

### Deployment Order

Apply manifests in dependency order:

```bash
# 1. Namespace & RBAC
kubectl apply -f deployment/k8s/namespace.yaml

# 2. Data tier (StatefulSets)
kubectl apply -f deployment/k8s/postgres-statefulset.yaml
kubectl apply -f deployment/k8s/minio-statefulset.yaml

# 3. Cache tier
kubectl apply -f deployment/k8s/redis-deployment.yaml

# 4. Infrastructure services
kubectl apply -f deployment/k8s/martin-deployment.yaml
kubectl apply -f deployment/k8s/keycloak-deployment.yaml

# 5. Application tier
kubectl apply -f deployment/k8s/api-deployment.yaml
kubectl apply -f deployment/k8s/worker-deployment.yaml

# 6. Ingress
kubectl apply -f deployment/k8s/ingress.yaml
```

### K8s Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│               Namespace: bhusynch-system                         │
│                                                                  │
│  StatefulSets:                                                   │
│    postgres (1 replica, 100Gi PVC, PostGIS 16-3.4)              │
│    minio    (1 replica, 200Gi PVC, S3 object store)             │
│                                                                  │
│  Deployments:                                                    │
│    redis    (1 replica, 1Gi memory limit)                        │
│    martin   (2 replicas, vector tile serving)                    │
│    keycloak (1 replica, OIDC identity provider)                  │
│    api      (3 replicas, FastAPI + OGC endpoints)                │
│    worker   (2 replicas, Celery + GPU node affinity)             │
│                                                                  │
│  Ingress:                                                        │
│    NGINX Ingress Controller with TLS termination                 │
│    Routes: /, /api, /ogc, /auth, /tiles, /storage               │
└─────────────────────────────────────────────────────────────────┘
```

### GPU Node Scheduling (Worker Pods)

The worker deployment includes GPU node affinity for GeoAI inference:

```yaml
affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
            - key: nvidia.com/gpu.product
              operator: In
              values:
                - NVIDIA-A10G
                - NVIDIA-L4
```

Resource requests for GPU workers:
- `nvidia.com/gpu: 1` per pod
- 8 Gi RAM, 4 CPU cores
- Tolerates `gpu-node` taints

### Secrets Management

Create Kubernetes secrets before deploying:

```bash
kubectl create secret generic bhusynch-db-credentials \
  --from-literal=POSTGRES_USER=bhusynch \
  --from-literal=POSTGRES_PASSWORD=<password> \
  -n bhusynch-system

kubectl create secret generic bhusynch-redis-credentials \
  --from-literal=REDIS_PASSWORD=<password> \
  -n bhusynch-system

kubectl create secret generic bhusynch-minio-credentials \
  --from-literal=MINIO_ROOT_USER=bhusynch_minio \
  --from-literal=MINIO_ROOT_PASSWORD=<password> \
  -n bhusynch-system

kubectl create secret generic bhusynch-keycloak-credentials \
  --from-literal=KEYCLOAK_ADMIN=admin \
  --from-literal=KEYCLOAK_ADMIN_PASSWORD=<password> \
  -n bhusynch-system
```

---

## 7. Service Reference

### Port Mapping

| Service    | Container Port | Default Host Port | Protocol |
| :--------- | :------------- | :---------------- | :------- |
| PostgreSQL | 5432           | 5432              | TCP      |
| Redis      | 6379           | 6379              | TCP      |
| MinIO API  | 9000           | 9000              | HTTP     |
| MinIO UI   | 9001           | 9001              | HTTP     |
| Martin     | 3000           | 3000              | HTTP     |
| Keycloak   | 8080           | 8080              | HTTP     |
| API        | 8000           | 8000              | HTTP     |
| Frontend   | 80             | 80                | HTTP     |

### Docker Network

All services communicate over the `bhusynch-network` bridge network. Internal service discovery uses Docker DNS (e.g., `postgres:5432`, `redis:6379`).

---

## 8. SSL & Ingress Configuration

### NGINX Reverse Proxy

The frontend NGINX configuration at `deployment/nginx/default.conf` handles:

- **Static file serving** for the 3D Web-GIS console and Mobile PWA
- **API reverse proxy** (`/api/` → `bhusynch-api:8000`)
- **OGC endpoint proxy** (`/ogc/` → `bhusynch-api:8000`)
- **Tile server proxy** (`/tiles/` → `bhusynch-martin:3000`)
- **Keycloak proxy** (`/auth/` → `bhusynch-keycloak:8080`)
- **MinIO proxy** (`/storage/` → `bhusynch-minio:9000`)
- **Security headers** (CSP, HSTS, X-Frame-Options, XSS protection)
- **Gzip compression** for JSON, MVT, GeoJSON, JavaScript, CSS
- **PWA support** with Service Worker and manifest caching rules

### Kubernetes TLS

The K8s ingress manifest supports TLS via cert-manager:

```yaml
tls:
  - hosts:
      - bhusynch.gov.in
      - api.bhusynch.gov.in
    secretName: bhusynch-tls-cert
```

Annotate for automatic certificate provisioning:

```yaml
annotations:
  cert-manager.io/cluster-issuer: "letsencrypt-prod"
```

---

## 9. Database Initialization

### Automatic Schema Bootstrap

The PostgreSQL container automatically executes `sql/init.sql` on first startup via the Docker entrypoint mechanism:

```yaml
volumes:
  - ./sql/init.sql:/docker-entrypoint-initdb.d/01_init.sql:ro
```

### Schema Contents

The initialization script creates:

1. **PostGIS Extensions:** `postgis`, `uuid-ossp`
2. **`cadastral_parcels`** — Authoritative parcel boundaries (EPSG:7755 geometry, ULPIN, Three-Truths provenance)
3. **`parcel_vertices`** — Vertex-level error covariance ellipses (σ-major, σ-minor, orientation)
4. **`revenue_ownership_records`** — Legal RoR/Jamabandi ownership registry
5. **`spatial_conflicts`** — Detected discrepancies and adjudication tracking
6. **`cadastral_audit_ledger`** — SHA3-256 Merkle chain immutable provenance log

### Manual Re-initialization

```bash
# Drop and recreate (WARNING: destroys all data)
docker exec -i bhusynch-postgres psql -U bhusynch -d bhusynch_cadastral < sql/init.sql
```

---

## 10. Storage & Object Store (MinIO)

### Bucket Organization

Create the required buckets after first deployment:

```bash
# Using MinIO Client (mc)
docker exec bhusynch-minio mc alias set local http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD

docker exec bhusynch-minio mc mb local/cog-geotiffs        # Cloud Optimized GeoTIFFs
docker exec bhusynch-minio mc mb local/las-pointclouds      # LAS/LAZ point cloud data
docker exec bhusynch-minio mc mb local/scanned-documents    # Scanned RoR/Sajra uploads
docker exec bhusynch-minio mc mb local/model-weights        # SAM-Geo, LightGlue, LayoutLMv3 weights
docker exec bhusynch-minio mc mb local/export-outputs       # Generated dossiers and reports
```

### Data Backup

```bash
# PostgreSQL backup
docker exec bhusynch-postgres pg_dump -U bhusynch -Fc bhusynch_cadastral > backup_$(date +%Y%m%d).dump

# MinIO sync to external storage
mc mirror local/ /backup/minio/ --overwrite
```

---

## 11. Monitoring & Health Checks

### Docker Compose Health Checks

All critical services have built-in health checks:

| Service    | Health Check Command                                              | Interval |
| :--------- | :---------------------------------------------------------------- | :------- |
| PostgreSQL | `pg_isready -U bhusynch -d bhusynch_cadastral`                   | 15s      |
| Redis      | `redis-cli -a $REDIS_PASSWORD ping`                               | 15s      |
| MinIO      | `mc ready local`                                                  | 30s      |
| API        | `GET /health` (if implemented) or container readiness              | 30s      |

### Kubernetes Health Probes

All K8s deployments include:

- **Liveness probes** — Restart unhealthy pods
- **Readiness probes** — Remove from service until ready
- **Startup probes** — Allow slow-starting services (Keycloak, PostgreSQL)

### Log Aggregation

```bash
# Docker Compose — follow all service logs
docker compose -f deployment/docker-compose.yml logs -f

# Docker Compose — follow specific service
docker compose -f deployment/docker-compose.yml logs -f api worker

# Kubernetes — follow API logs
kubectl logs -f deployment/bhusynch-api -n bhusynch-system

# Kubernetes — follow worker logs
kubectl logs -f deployment/bhusynch-worker -n bhusynch-system
```

---

## 12. Troubleshooting

### Common Issues

#### PostgreSQL fails to start
```bash
# Check logs
docker logs bhusynch-postgres

# Verify init.sql syntax
docker exec -it bhusynch-postgres psql -U bhusynch -d bhusynch_cadastral -c "\dt"
```

#### Celery worker cannot connect to Redis
```bash
# Verify Redis is healthy
docker exec bhusynch-redis redis-cli -a $REDIS_PASSWORD ping

# Check REDIS_URL in worker environment
docker exec bhusynch-worker env | grep REDIS
```

#### MinIO health check fails
```bash
# Verify MinIO is accessible
curl http://localhost:9000/minio/health/live

# Check MinIO logs
docker logs bhusynch-minio
```

#### Martin cannot connect to PostGIS
```bash
# Ensure PostGIS tables exist with geometry columns
docker exec bhusynch-postgres psql -U bhusynch -d bhusynch_cadastral \
  -c "SELECT f_table_name, f_geometry_column FROM geometry_columns;"
```

#### K8s pods stuck in Pending (GPU worker)
```bash
# Check node GPU availability
kubectl describe nodes | grep -A5 "nvidia.com/gpu"

# Check pod events
kubectl describe pod -l app=bhusynch-worker -n bhusynch-system
```

### Service Restart

```bash
# Restart a single service (Docker Compose)
docker compose -f deployment/docker-compose.yml restart api

# Rolling restart (Kubernetes)
kubectl rollout restart deployment/bhusynch-api -n bhusynch-system
```

### Full System Reset (Development Only)

```bash
# WARNING: Destroys all data
docker compose -f deployment/docker-compose.yml down -v
docker compose -f deployment/docker-compose.yml up --build
```

---

*Last updated: September 2026*
*Architecture Reference: [PLAN_ALPHA_SYSTEM_ARCHITECTURE.md](../PLAN_ALPHA_SYSTEM_ARCHITECTURE.md)*
