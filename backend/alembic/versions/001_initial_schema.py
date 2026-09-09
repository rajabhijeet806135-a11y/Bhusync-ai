"""
001_initial_schema — Initial BhuSynch AI Database Schema
=========================================================
Creates all 5 tables from Section 3 DDL of Plan Alpha:
  1. cadastral_parcels
  2. parcel_vertices
  3. revenue_ownership_records
  4. spatial_conflicts
  5. cadastral_audit_ledger

Revision ID: 001_initial
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geometry

# Revision identifiers
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable PostGIS extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # 1. cadastral_parcels
    op.create_table(
        "cadastral_parcels",
        sa.Column("parcel_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("uuid_generate_v4()")),
        sa.Column("ulpin", sa.String(14), unique=True, nullable=True),
        sa.Column("state_code", sa.String(2), nullable=False),
        sa.Column("district_code", sa.String(3), nullable=False),
        sa.Column("village_code", sa.String(6), nullable=False),
        sa.Column("khasra_no", sa.String(50), nullable=False),
        sa.Column("khata_no", sa.String(50), nullable=True),
        sa.Column("legal_area_sqm", sa.Numeric(12, 4), nullable=False),
        sa.Column("observed_area_sqm", sa.Numeric(12, 4), nullable=True),
        sa.Column("status", sa.String(30), server_default=sa.text("'PROVISIONAL'")),
        sa.Column("geom", Geometry(geometry_type="POLYGON", srid=7755), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_parcels_geom", "cadastral_parcels", ["geom"], postgresql_using="gist")

    # 2. parcel_vertices
    op.create_table(
        "parcel_vertices",
        sa.Column("vertex_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("uuid_generate_v4()")),
        sa.Column("parcel_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("cadastral_parcels.parcel_id", ondelete="CASCADE"), nullable=False),
        sa.Column("vertex_index", sa.Integer, nullable=False),
        sa.Column("sigma_major_axis_m", sa.Numeric(6, 4), nullable=False),
        sa.Column("sigma_minor_axis_m", sa.Numeric(6, 4), nullable=False),
        sa.Column("orientation_deg", sa.Numeric(5, 2), nullable=False),
        sa.Column("confidence_score", sa.Numeric(4, 3), nullable=False),
        sa.Column("geom", Geometry(geometry_type="POINT", srid=7755), nullable=False),
    )
    op.create_index("idx_vertices_geom", "parcel_vertices", ["geom"], postgresql_using="gist")

    # 3. revenue_ownership_records
    op.create_table(
        "revenue_ownership_records",
        sa.Column("record_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("uuid_generate_v4()")),
        sa.Column("parcel_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("cadastral_parcels.parcel_id"), nullable=False),
        sa.Column("owner_name_vernacular", sa.Text, nullable=False),
        sa.Column("owner_name_english", sa.Text, nullable=False),
        sa.Column("father_spouse_name", sa.Text, nullable=True),
        sa.Column("share_fraction", sa.String(20), server_default=sa.text("'1/1'")),
        sa.Column("land_type", sa.String(50), nullable=True),
        sa.Column("encumbrance_status", sa.Text, nullable=True),
        sa.Column("ocr_confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("raw_document_url", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # 4. spatial_conflicts
    op.create_table(
        "spatial_conflicts",
        sa.Column("conflict_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("uuid_generate_v4()")),
        sa.Column("parcel_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("cadastral_parcels.parcel_id"), nullable=False),
        sa.Column("conflict_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("discrepancy_area_sqm", sa.Numeric(10, 4), nullable=True),
        sa.Column("disputed_geometry", Geometry(geometry_type="GEOMETRY", srid=7755), nullable=False),
        sa.Column("evidence_payload", postgresql.JSONB, nullable=False),
        sa.Column("adjudication_status", sa.String(30),
                   server_default=sa.text("'PENDING_OFFICER_REVIEW'")),
        sa.Column("assigned_officer_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_conflicts_geom", "spatial_conflicts", ["disputed_geometry"], postgresql_using="gist")

    # 5. cadastral_audit_ledger
    op.create_table(
        "cadastral_audit_ledger",
        sa.Column("entry_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("ulpin", sa.String(14), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("officer_id", sa.String(100), nullable=False),
        sa.Column("prev_merkle_hash", sa.String(64), nullable=False),
        sa.Column("current_hash", sa.String(64), nullable=False),
        sa.Column("dsc_signature", sa.Text, nullable=False),
        sa.Column("payload_snapshot", postgresql.JSONB, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_audit_ulpin", "cadastral_audit_ledger", ["ulpin"])


def downgrade() -> None:
    op.drop_table("cadastral_audit_ledger")
    op.drop_table("spatial_conflicts")
    op.drop_table("revenue_ownership_records")
    op.drop_table("parcel_vertices")
    op.drop_table("cadastral_parcels")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
    op.execute("DROP EXTENSION IF EXISTS postgis")
