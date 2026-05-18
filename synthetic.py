from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Módulos activos
    enable_ela: bool = True
    enable_noise: bool = True
    enable_sharpness: bool = True
    enable_copy_move: bool = False
    enable_jpeg: bool = True
    enable_metadata: bool = True

    # Parámetros ELA
    ela_quality: int = 90
    ela_amplify: int = 15
    ela_region_block: int = 64
    ela_region_sigma: float = 2.5

    # Parámetros Noise
    noise_block_size: int = 32
    noise_threshold_sigma: float = 2.0

    # Parámetros Sharpness
    sharp_block_size: int = 32
    sharp_anomaly_sigma: float = 2.5

    # Pesos del scoring
    score_weight_ela: float = 0.22
    score_weight_noise: float = 0.18
    score_weight_jpeg: float = 0.15
    score_weight_edge: float = 0.10
    score_weight_blur: float = 0.10
    score_weight_resamp: float = 0.10
    score_weight_copymove: float = 0.15
    score_meta_bonus: float = 0.20
    score_meta_only_cap: float = 0.55

    # Thresholds de decisión
    threshold_medium: float = 0.31
    threshold_high: float = 0.61
    threshold_manual: float = 0.81

    # Sistema
    output_dir: str = "/outputs"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator(
        "score_weight_ela",
        "score_weight_noise",
        "score_weight_jpeg",
        "score_weight_edge",
        "score_weight_blur",
        "score_weight_resamp",
        "score_weight_copymove",
    )
    @classmethod
    def peso_valido(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Peso fuera de rango [0,1]: {v}")
        return v

    @field_validator("threshold_manual")
    @classmethod
    def thresholds_coherentes(cls, v: float, info: Any) -> float:
        medium = info.data.get("threshold_medium", 0.31)
        high = info.data.get("threshold_high", 0.61)
        if not (medium < high < v <= 1.0):
            raise ValueError("Thresholds deben cumplir: medium < high < manual <= 1.0")
        return v


settings = Settings()
