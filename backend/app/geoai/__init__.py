"""
BhuSynch AI — GeoAI Package
==============================
AI/ML model interfaces for all subsystems.

Models:
- SAM-Geo ViT-H: Boundary segmentation (Subsystem 3)
- SuperPoint: Keypoint detection (Subsystem 1)
- LightGlue: Feature matching (Subsystem 1)
- LayoutLMv3: Document table segmentation (Subsystem 2)
- TrOCR Indic: Indic script OCR (Subsystem 2)
- Sarvam-1: Indic LLM for entity parsing (Subsystem 2)
- ChangeFormer: Bitemporal change detection (Subsystem 5)
- Graph Neural: GIN/GNN conflation (Subsystem 3)
"""

from app.geoai.base_model import GeoAIModel
from app.geoai.model_registry import ModelRegistry

__all__ = ["GeoAIModel", "ModelRegistry"]
