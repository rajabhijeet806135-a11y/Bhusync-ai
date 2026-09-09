"""
BhuSynch AI — Model Registry
===============================
Singleton registry for lazy-loading, caching, and managing
all GeoAI models in the Ray Inference Cluster.

Supports TensorRT and ONNX Runtime optimization paths
as specified in Section 1 architecture.
"""

import threading
from typing import Dict, Optional, Type

import structlog

from app.config import settings
from app.geoai.base_model import GeoAIModel, ModelConfig

logger = structlog.get_logger(__name__)


class ModelRegistry:
    """
    Thread-safe singleton model registry with lazy loading.

    Maps to: Ray GeoAI Inference Cluster (Section 1)
    - SAM-Geo, LightGlue, LayoutLMv3 model pools
    - TensorRT / ONNX Runtime optimization
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._models: Dict[str, GeoAIModel] = {}
                cls._instance._model_classes: Dict[str, Type[GeoAIModel]] = {}
                cls._instance._configs: Dict[str, ModelConfig] = {}
                cls._instance._initialized = False
            return cls._instance

    def initialize(self) -> None:
        """Register all model classes from the architecture."""
        if self._initialized:
            return

        from app.geoai.sam_geo import SAMGeoModel
        from app.geoai.superpoint import SuperPointModel
        from app.geoai.lightglue import LightGlueModel
        from app.geoai.layout_lmv3 import LayoutLMv3Model
        from app.geoai.trocr_indic import TrOCRIndicModel
        from app.geoai.sarvam_llm import SarvamLLMModel
        from app.geoai.changeformer import ChangeFormerModel
        from app.geoai.graph_neural import GraphNeuralModel

        self._model_classes = {
            "sam_geo": SAMGeoModel,
            "superpoint": SuperPointModel,
            "lightglue": LightGlueModel,
            "layoutlmv3": LayoutLMv3Model,
            "trocr_indic": TrOCRIndicModel,
            "sarvam_llm": SarvamLLMModel,
            "changeformer": ChangeFormerModel,
            "graph_neural": GraphNeuralModel,
        }

        self._configs = {
            "sam_geo": ModelConfig(
                name="SAM-Geo-ViT-H", version="1.0",
                checkpoint_path=settings.SAM_GEO_CHECKPOINT,
                use_tensorrt=settings.USE_TENSORRT,
            ),
            "superpoint": ModelConfig(
                name="SuperPoint", version="v1",
                checkpoint_path=settings.SUPERPOINT_WEIGHTS,
            ),
            "lightglue": ModelConfig(
                name="LightGlue", version="outdoor",
                checkpoint_path=settings.LIGHTGLUE_WEIGHTS,
            ),
            "layoutlmv3": ModelConfig(
                name="LayoutLMv3", version="base",
                checkpoint_path=settings.LAYOUTLMV3_MODEL,
            ),
            "trocr_indic": ModelConfig(
                name="TrOCR-Indic", version="base",
                checkpoint_path=settings.TROCR_MODEL,
            ),
            "sarvam_llm": ModelConfig(
                name="Sarvam-1", version="1.0",
                checkpoint_path=settings.SARVAM_MODEL,
            ),
            "changeformer": ModelConfig(
                name="ChangeFormer", version="levir",
                checkpoint_path=settings.CHANGEFORMER_WEIGHTS,
            ),
            "graph_neural": ModelConfig(
                name="GIN-Conflation", version="1.0",
            ),
        }

        self._initialized = True
        logger.info("model_registry_initialized", models=list(self._model_classes.keys()))

    def get(self, model_name: str, auto_load: bool = True) -> GeoAIModel:
        """
        Get a model by name. Lazily loads on first access.

        Parameters:
            model_name: One of: sam_geo, superpoint, lightglue, layoutlmv3,
                       trocr_indic, sarvam_llm, changeformer, graph_neural
            auto_load: If True, automatically load model weights
        """
        if not self._initialized:
            self.initialize()

        if model_name not in self._model_classes:
            raise ValueError(
                f"Unknown model: {model_name}. "
                f"Available: {list(self._model_classes.keys())}"
            )

        if model_name not in self._models:
            config = self._configs.get(model_name)
            model_cls = self._model_classes[model_name]
            model = model_cls(config) if config else model_cls()

            if auto_load:
                model.load()

            self._models[model_name] = model
            logger.info("model_cached", name=model_name)

        return self._models[model_name]

    def unload(self, model_name: str) -> None:
        """Unload a specific model from memory."""
        if model_name in self._models:
            self._models[model_name].unload()
            del self._models[model_name]
            logger.info("model_unloaded", name=model_name)

    def unload_all(self) -> None:
        """Unload all models from memory."""
        for name in list(self._models.keys()):
            self.unload(name)

    def status(self) -> Dict[str, bool]:
        """Return loading status of all registered models."""
        if not self._initialized:
            self.initialize()
        return {
            name: name in self._models and self._models[name].is_loaded
            for name in self._model_classes
        }
