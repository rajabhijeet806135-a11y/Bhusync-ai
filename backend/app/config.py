"""
BhuSynch AI — Configuration Module
====================================
Centralized Pydantic Settings for all service connections,
data paths, model registry, and deployment parameters.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    All settings map directly to the Plan Alpha System Architecture.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────
    APP_NAME: str = "BhuSynch AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── PostgreSQL + PostGIS (Distributed Spatial Storage Core) ──────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "bhusynch"
    POSTGRES_PASSWORD: str = "bhusynch_secure_2024"
    POSTGRES_DB: str = "bhusynch_cadastral"
    POSTGRES_SRID: int = 7755  # EPSG:7755 — India-centric CRS

    DATABASE_URL_OVERRIDE: Optional[str] = Field(default=None, alias="DATABASE_URL")

    @property
    def DATABASE_URL(self) -> str:
        """Async PostgreSQL connection string for SQLAlchemy."""
        if self.DATABASE_URL_OVERRIDE:
            url = self.DATABASE_URL_OVERRIDE
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Synchronous PostgreSQL connection string for Alembic migrations."""
        if self.DATABASE_URL_OVERRIDE:
            url = self.DATABASE_URL_OVERRIDE
            if url.startswith("postgresql+asyncpg://"):
                url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
            return url
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Redis / RabbitMQ (Asynchronous Orchestration Layer) ──────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    @property
    def REDIS_URL(self) -> str:
        """Redis connection URL for Celery broker."""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    CELERY_BROKER_URL: Optional[str] = None  # Falls back to REDIS_URL
    CELERY_RESULT_BACKEND: Optional[str] = None

    @property
    def celery_broker(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    # ── MinIO Object Storage (S3 API — COGs, LAS/LAZ) ───────────────
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "bhusynch_minio"
    MINIO_SECRET_KEY: str = "bhusynch_minio_secret"
    MINIO_BUCKET_COG: str = "cog-geotiffs"
    MINIO_BUCKET_POINTCLOUD: str = "las-pointclouds"
    MINIO_BUCKET_DOCUMENTS: str = "scanned-documents"
    MINIO_USE_SSL: bool = False

    # ── Keycloak OIDC (API Gateway Security) ─────────────────────────
    KEYCLOAK_SERVER_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "bhusynch"
    KEYCLOAK_CLIENT_ID: str = "bhusynch-api"
    KEYCLOAK_CLIENT_SECRET: str = ""
    KEYCLOAK_ADMIN_ROLE: str = "revenue_officer"
    KEYCLOAK_VERIFY_SSL: bool = False

    # ── Data Assets Path ─────────────────────────────────────────────
    DATA_ASSETS_PATH: Path = Path(r"C:\Users\rajab\Desktop\data_assets")

    # ── GeoAI Model Registry ────────────────────────────────────────
    MODEL_CACHE_DIR: Path = Path("./model_cache")
    SAM_GEO_CHECKPOINT: str = "sam_vit_h_4b8939.pth"
    SUPERPOINT_WEIGHTS: str = "superpoint_v1.pth"
    LIGHTGLUE_WEIGHTS: str = "lightglue_outdoor.pth"
    LAYOUTLMV3_MODEL: str = "microsoft/layoutlmv3-base"
    TROCR_MODEL: str = "microsoft/trocr-base-handwritten"
    SARVAM_MODEL: str = "sarvamai/sarvam-1"
    CHANGEFORMER_WEIGHTS: str = "changeformer_levir.pth"
    USE_TENSORRT: bool = False
    USE_ONNX_RUNTIME: bool = False
    RAY_NUM_WORKERS: int = 4
    RAY_GPU_PER_WORKER: float = 0.5

    # ── Martin Tile Server ───────────────────────────────────────────
    MARTIN_URL: str = "http://localhost:3000"

    # ── CORS & API ───────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080", "*"]
    API_PREFIX: str = ""

    # ── Cryptographic Provenance ─────────────────────────────────────
    DSC_PRIVATE_KEY_PATH: Optional[str] = None
    DSC_CERTIFICATE_PATH: Optional[str] = None
    MERKLE_GENESIS_HASH: str = "0" * 64  # 64-char zero hash as genesis block


settings = Settings()
