from pathlib import Path
from typing import Any

from .modules.ingestion import ingest_file
from .modules.metadata import analyze_metadata
from .modules.ela import compute_ela
from .modules.noise import analyze_noise
from .modules.sharpness import analyze_sharpness
from .modules.jpeg_analysis import analyze_jpeg
from .modules.fusion import fuse_heatmaps
from .modules.scoring import compute_score
from .settings import settings
from .schemas import MetadataResult

_FINDING_DESCRIPTIONS = {
    'ela_anomaly': 'Inconsistencia localizada de nivel de error de compresión',
    'noise_anomaly': 'Distribución de ruido estadísticamente anómala en esta región',
    'sharpness_anomaly': 'Nitidez local incongruente respecto al entorno',
}

def _serialize_metadata(meta: MetadataResult | None) -> dict[str, Any]:
    if not meta:
        return {}
    return {
        'exif_present': meta.exif_present,
        'xmp_present': meta.xmp_present,
        'software': meta.software,
        'creation_date': meta.creation_date,
        'modification_date': meta.modification_date,
        'dpi': meta.dpi,
        'color_space': meta.color_space,
    }

def run_pipeline(image_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Ejecuta el pipeline completo y devuelve el dict de respuesta.
    
    Args:
        image_path: Ruta al fichero temporal con los bytes de la imagen.
        config: Configuración de qué módulos activar.
        
    Returns:
        Diccionario listo para serializar a JSON.
    """
    cfg = {
        'enable_ela': settings.enable_ela,
        'enable_noise': settings.enable_noise,
        'enable_sharpness': settings.enable_sharpness,
        'enable_copy_move': settings.enable_copy_move,
        'enable_jpeg': settings.enable_jpeg,
        'enable_metadata': settings.enable_metadata,
        **config,
    }
    
    ingested = ingest_file(image_path)
    meta_result = analyze_metadata(image_path, ingested.sha256) if cfg['enable_metadata'] else None
    ela_result = compute_ela(ingested.image_rgb) if cfg['enable_ela'] else None
    noise_result = analyze_noise(ingested.image_gray) if cfg['enable_noise'] else None
    sharp_result = analyze_sharpness(ingested.image_gray) if cfg['enable_sharpness'] else None
    jpeg_result = analyze_jpeg(ingested.image_rgb, ingested.is_jpeg) if cfg['enable_jpeg'] else None
    
    maps = {}
    if ela_result is not None:
        maps['ela'] = ela_result.ela_image[:, :, 0]
    if noise_result is not None:
        maps['noise'] = noise_result.noise_map
    if sharp_result is not None:
        maps['sharpness'] = sharp_result.sharpness_map
        
    fusion = fuse_heatmaps(maps) if maps else None
    
    score = compute_score(
        ela=ela_result.ela_score if ela_result else 0.0,
        noise=noise_result.noise_score if noise_result else 0.0,
        blur=sharp_result.blur_score if sharp_result else 0.0,
        jpeg=jpeg_result.jpeg_score if jpeg_result else 0.0,
        metadata=meta_result.metadata_risk_score if meta_result else 0.0,
    )
    
    visual_findings: list[dict[str, Any]] = []
    for module_result, finding_type in [
        (ela_result, 'ela_anomaly'),
        (noise_result, 'noise_anomaly'),
        (sharp_result, 'sharpness_anomaly'),
    ]:
        if module_result and hasattr(module_result, 'anomalous_regions'):
            for (x, y, w, h, s) in module_result.anomalous_regions:
                visual_findings.append({
                    'type': finding_type,
                    'region': [x, y, w, h],
                    'score': round(s, 3),
                    'description': _FINDING_DESCRIPTIONS[finding_type],
                })
                
    limitations: list[str] = []
    for r in [ela_result, noise_result, sharp_result, meta_result]:
        if r and hasattr(r, 'limitations'):
            limitations.extend(r.limitations)
    limitations = list(dict.fromkeys(limitations))
    if not limitations:
        # Just in case to ensure it's not empty for tests
        limitations.append("El análisis forense es probabilístico y no definitivo.")

    return {
        'sha256': ingested.sha256,
        'mime_detected': ingested.mime_detected,
        'extension_declared': ingested.extension_declared,
        'extension_mismatch': ingested.extension_mismatch,
        'width_px': ingested.width,
        'height_px': ingested.height,
        'decision': score.decision,
        'scores': {
            'ela_score': round(score.ela_score, 3),
            'noise_inconsistency_score': round(score.noise_score, 3),
            'jpeg_double_compression_score': round(score.jpeg_score, 3),
            'edge_inconsistency_score': round(score.edge_score, 3),
            'blur_inconsistency_score': round(score.blur_score, 3),
            'resampling_score': round(score.resampling_score, 3),
            'metadata_technical_score': round(score.metadata_score, 3),
            'container_structure_score': round(score.container_score, 3),
            'final_score': round(score.final_score, 3),
        },
        'visual_findings': visual_findings,
        'metadata_findings': [vars(f) for f in meta_result.findings] if meta_result else [],
        'metadata': _serialize_metadata(meta_result),
        'limitations': limitations,
    }
