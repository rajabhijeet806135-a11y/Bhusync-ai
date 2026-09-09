"""
BhuSynch AI — Celery Application Configuration
=================================================
Asynchronous Orchestration Layer (Section 1):
FastAPI → Celery Task Producer → Redis/RabbitMQ Queue → Distributed Workers
"""

from celery import Celery

from app.config import settings

# ── Celery Application ───────────────────────────────────────────────
celery_app = Celery(
    "bhusynch_workers",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
)

# ── Configuration ────────────────────────────────────────────────────
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    worker_concurrency=4,

    # Task routing — maps to architecture worker tiers
    task_routes={
        "app.workers.geodesy_tasks.*": {"queue": "geodesy"},
        "app.workers.document_ai_tasks.*": {"queue": "document_ai"},
        "app.workers.conflation_tasks.*": {"queue": "conflation"},
        "app.workers.arbitration_tasks.*": {"queue": "arbitration"},
        "app.workers.topology_tasks.*": {"queue": "topology"},
    },

    # Task result expiration
    result_expires=86400,  # 24 hours

    # Rate limiting
    task_default_rate_limit="10/m",

    # Retry policy
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# ── Auto-discover tasks ──────────────────────────────────────────────
celery_app.autodiscover_tasks([
    "app.workers.geodesy_tasks",
    "app.workers.document_ai_tasks",
    "app.workers.conflation_tasks",
    "app.workers.arbitration_tasks",
    "app.workers.topology_tasks",
])
