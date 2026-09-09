"""
BhuSynch AI — Sarvam-1 Indic LLM Interface
=============================================
Subsystem 2: Multilingual Document AI & ULPIN Generation

Sarvam-1 / Indic-LLM parses ownership shares and standardizes
vernacular area units (Bigha, Gunta, Katha, Biswa) into metric m².

Also computes canonical name identity vectors for name resolution (Section 2.2):
E_name = [E_phonetic, E_script, E_translit, E_context]
S_name = w₁ S_edit + w₂ S_phonetic + w₃ S_translit + w₄ S_context

Pipeline: [TrOCR Indic] → [Sarvam-1 LLM] → [Entity Tuples] → [ULPIN Encoder]
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import structlog

from app.geoai.base_model import GeoAIModel, InferenceResult, ModelConfig

logger = structlog.get_logger(__name__)


# Vernacular area unit conversion factors to square meters
AREA_UNIT_CONVERSIONS = {
    "bigha": 2529.285264,     # 1 Bigha = 2529.285264 m² (varies by state)
    "biswa": 126.46,          # 1 Biswa = 1/20 Bigha ≈ 126.46 m²
    "katha": 126.46,          # 1 Katha ≈ 126.46 m² (Bihar/UP)
    "gunta": 101.17,          # 1 Gunta = 101.17 m² (Karnataka/Maharashtra)
    "cent": 40.4686,          # 1 Cent = 40.4686 m² (Kerala/Tamil Nadu)
    "acre": 4046.8564,        # 1 Acre = 4046.8564 m²
    "hectare": 10000.0,       # 1 Hectare = 10000 m²
    "marla": 25.2929,         # 1 Marla = 25.2929 m² (Punjab)
    "kanal": 505.857,         # 1 Kanal = 505.857 m² (Punjab/J&K)
    "ground": 222.967,        # 1 Ground = 222.967 m² (Tamil Nadu)
    "dismil": 40.4686,        # 1 Dismil = 40.4686 m²
    "dhur": 16.929,           # 1 Dhur = 16.929 m² (Bihar)
}


@dataclass
class OwnerEntity:
    """Extracted owner entity from RoR document."""
    owner_name_vernacular: str
    owner_name_english: str
    father_spouse_name: Optional[str] = None
    share_fraction: str = "1/1"
    land_type: Optional[str] = None          # Khari, Bagayat, Gair Mumkin
    area_value: Optional[float] = None        # Numerical area value
    area_unit: Optional[str] = None           # Original vernacular unit
    area_sqm: Optional[float] = None          # Standardized to m²
    encumbrance: Optional[str] = None


@dataclass
class NameVector:
    """
    Canonical Name Identity Vector for cross-lingual name resolution.
    Formula (Section 2.2):
    E_name = [E_phonetic, E_script, E_translit, E_context]
    """
    phonetic_embedding: np.ndarray     # Phonetic representation
    script_embedding: np.ndarray       # Script-specific embedding
    translit_embedding: np.ndarray     # Transliteration embedding
    context_embedding: np.ndarray      # Contextual embedding

    @property
    def full_vector(self) -> np.ndarray:
        return np.concatenate([
            self.phonetic_embedding,
            self.script_embedding,
            self.translit_embedding,
            self.context_embedding,
        ])


class SarvamLLMModel(GeoAIModel):
    """
    Sarvam-1: Indic Large Language Model for Entity Extraction.

    Capabilities (Section 2.2):
    1. Parse ownership shares from OCR text
    2. Standardize vernacular area units to metric m²
    3. Generate canonical name identity vectors for deduplication
    4. Classify land types (Khari, Bagayat, Gair Mumkin)
    5. Extract encumbrance and mutation details

    Name similarity scoring (Section 2.2):
    S_name = w₁ S_edit + w₂ S_phonetic + w₃ S_translit + w₄ S_context
    """

    def __init__(self, config: ModelConfig = None):
        if config is None:
            config = ModelConfig(
                name="Sarvam-1",
                version="1.0",
                checkpoint_path="sarvamai/sarvam-1",
                device="cuda",
                extra={
                    "max_tokens": 2048,
                    "temperature": 0.1,
                    "name_similarity_weights": {
                        "w1_edit": 0.25,
                        "w2_phonetic": 0.30,
                        "w3_translit": 0.25,
                        "w4_context": 0.20,
                    },
                },
            )
        super().__init__(config)

    def load(self) -> None:
        """Load Sarvam-1 LLM."""
        logger.info("loading_sarvam", model=self.config.checkpoint_path)

        # Placeholder — in production:
        # from transformers import AutoTokenizer, AutoModelForCausalLM
        # self.tokenizer = AutoTokenizer.from_pretrained(self.config.checkpoint_path)
        # self.model = AutoModelForCausalLM.from_pretrained(self.config.checkpoint_path)
        # self.model.to(self.config.device).eval()

        self.is_loaded = True
        logger.info("sarvam_loaded")

    def preprocess(self, input_data: Any) -> Dict[str, Any]:
        """Preprocess OCR text for entity extraction."""
        if isinstance(input_data, str):
            text = input_data
        elif isinstance(input_data, dict):
            text = input_data.get("text", "")
        elif isinstance(input_data, list):
            text = "\n".join(str(item) for item in input_data)
        else:
            text = str(input_data)

        return {"text": text}

    def predict(self, preprocessed: Dict[str, Any]) -> Dict[str, Any]:
        """Run Sarvam-1 entity extraction."""
        text = preprocessed["text"]
        logger.info("sarvam_inference", text_length=len(text))

        # Placeholder — returns mock entity tuples
        return {
            "entities": [
                {
                    "owner_name_vernacular": "राम प्रसाद शर्मा",
                    "owner_name_english": "Ram Prasad Sharma",
                    "father_spouse_name": "Shyam Lal Sharma",
                    "share_fraction": "1/2",
                    "land_type": "Khari",
                    "area_value": 2.5,
                    "area_unit": "bigha",
                    "encumbrance": None,
                }
            ],
            "raw_text": text,
        }

    def postprocess(self, raw_output: Dict[str, Any]) -> InferenceResult:
        """Convert raw entities to structured OwnerEntity objects."""
        owners = []
        for e in raw_output["entities"]:
            area_sqm = None
            if e.get("area_value") and e.get("area_unit"):
                unit = e["area_unit"].lower()
                if unit in AREA_UNIT_CONVERSIONS:
                    area_sqm = e["area_value"] * AREA_UNIT_CONVERSIONS[unit]

            owners.append(OwnerEntity(
                owner_name_vernacular=e["owner_name_vernacular"],
                owner_name_english=e["owner_name_english"],
                father_spouse_name=e.get("father_spouse_name"),
                share_fraction=e.get("share_fraction", "1/1"),
                land_type=e.get("land_type"),
                area_value=e.get("area_value"),
                area_unit=e.get("area_unit"),
                area_sqm=area_sqm,
                encumbrance=e.get("encumbrance"),
            ))

        return InferenceResult(
            predictions=owners,
            confidence=0.88,
            metadata={
                "model": "Sarvam-1",
                "num_entities": len(owners),
                "area_conversions": {o.area_unit: o.area_sqm for o in owners if o.area_sqm},
            },
        )

    @staticmethod
    def compute_name_similarity(
        name_vector_a: NameVector,
        name_vector_b: NameVector,
        weights: Dict[str, float] = None,
    ) -> float:
        """
        Compute name similarity using the canonical identity vector formula.

        Section 2.2:
        S_name = w₁ S_edit + w₂ S_phonetic + w₃ S_translit + w₄ S_context

        Parameters:
            name_vector_a: First name's identity vector
            name_vector_b: Second name's identity vector
            weights: Similarity component weights {w1, w2, w3, w4}

        Returns:
            Combined similarity score [0, 1]
        """
        if weights is None:
            weights = {"w1_edit": 0.25, "w2_phonetic": 0.30, "w3_translit": 0.25, "w4_context": 0.20}

        def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
            dot = np.dot(a, b)
            norm = np.linalg.norm(a) * np.linalg.norm(b)
            return float(dot / (norm + 1e-8))

        s_phonetic = cosine_sim(name_vector_a.phonetic_embedding, name_vector_b.phonetic_embedding)
        s_script = cosine_sim(name_vector_a.script_embedding, name_vector_b.script_embedding)
        s_translit = cosine_sim(name_vector_a.translit_embedding, name_vector_b.translit_embedding)
        s_context = cosine_sim(name_vector_a.context_embedding, name_vector_b.context_embedding)

        similarity = (
            weights["w1_edit"] * s_script
            + weights["w2_phonetic"] * s_phonetic
            + weights["w3_translit"] * s_translit
            + weights["w4_context"] * s_context
        )

        return float(np.clip(similarity, 0.0, 1.0))

    @staticmethod
    def convert_area_to_sqm(value: float, unit: str) -> Optional[float]:
        """
        Convert vernacular area units to metric square meters.
        Handles: Bigha, Gunta, Katha, Biswa, Cent, Acre, etc.
        """
        unit_lower = unit.lower().strip()
        if unit_lower in AREA_UNIT_CONVERSIONS:
            return value * AREA_UNIT_CONVERSIONS[unit_lower]
        logger.warning("unknown_area_unit", unit=unit)
        return None
