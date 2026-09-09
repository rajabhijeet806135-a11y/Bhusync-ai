-- =====================================================================
-- BhuSynch AI — PostgreSQL / PostGIS Database Schema (Section 3 DDL)
-- =====================================================================
-- National Urban Cadastral Intelligence Mesh
-- Problem Statement ID: SIH 26013
-- SRID: EPSG:7755 (India-centric projected CRS)
-- =====================================================================

-- Enable PostGIS & Vector Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================================
-- 1. Base Cadastral Parcels Table
-- =====================================================================
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

-- =====================================================================
-- 2. Vertex Error Covariance Table
-- =====================================================================
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

-- =====================================================================
-- 3. Legal RoR Ownership Registry
-- =====================================================================
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

-- =====================================================================
-- 4. Spatial Conflict Cases Table
-- =====================================================================
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

-- =====================================================================
-- 5. Immutable Merkle Audit Ledger
-- =====================================================================
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
CREATE INDEX idx_audit_ulpin ON cadastral_audit_ledger(ulpin);
