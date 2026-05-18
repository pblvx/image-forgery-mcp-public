import base64
import logging
import tempfile
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .pipeline import run_pipeline
from .settings import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "image-forgery-detector",
    dependencies=["numpy", "opencv-python-headless", "Pillow", "piexif", "python-magic", "pydantic-settings"]
)

@mcp.tool()
def analizar_imagen(
    imagen_base64: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Analiza una imagen en busca de indicios de manipulación digital.
    
    Args:
        imagen_base64: Imagen codificada en Base64.
        config: Diccionario opcional para activar/desactivar módulos.
        
    Returns:
        Diccionario con el informe forense completo.
    """
    logger.info('Recibida petición de análisis forense')
    try:
        image_bytes = base64.b64decode(imagen_base64)
    except Exception as exc:
        return {
            "error": "imagen_base64 no es Base64 válido",
            "detalle": str(exc)
        }
        
    with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = Path(tmp.name)
        
    try:
        result = run_pipeline(tmp_path, config or {})
    except Exception as exc:
        logger.exception("Error durante el análisis")
        return {
            "error": "Error interno durante el análisis",
            "detalle": str(exc)
        }
    finally:
        tmp_path.unlink(missing_ok=True)
        
    if 'scores' in result and 'final_score' in result['scores']:
        logger.info(
            'Análisis completado: score=%.3f decision=%s',
            result['scores']['final_score'],
            result.get('decision', 'unknown'),
        )
    return result

if __name__ == '__main__':
    mcp.run()
