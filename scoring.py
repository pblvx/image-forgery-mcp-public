import hashlib
from pathlib import Path
import magic
import numpy as np
from PIL import Image

from ..schemas import IngestionResult
from ..exceptions import UnsupportedFormatError


def ingest_file(image_path: Path) -> IngestionResult:
    """Read an image file and extract its basic properties and numpy arrays."""
    if not image_path.exists():
        raise FileNotFoundError(f"File {image_path} does not exist.")
        
    with open(image_path, "rb") as f:
        data = f.read()
        
    sha256 = hashlib.sha256(data).hexdigest()
    mime_detected = magic.from_buffer(data, mime=True)
    
    # We will derive the declared extension from the file path if provided
    extension_declared = image_path.suffix.lower().lstrip('.')
    if not extension_declared or extension_declared == 'bin':
        # Fallback to PIL format if we only have a temp binary file
        try:
            with Image.open(image_path) as img:
                fmt = img.format
                extension_declared = fmt.lower() if fmt else "unknown"
        except Exception:
            extension_declared = "unknown"

    if extension_declared == "jpg":
        extension_declared = "jpeg"
        
    expected_mime = f"image/{extension_declared}"
    # Edge case mappings
    if extension_declared == "unknown":
        extension_mismatch = False
    else:
        extension_mismatch = mime_detected != expected_mime

    try:
        with Image.open(image_path) as img:
            width, height = img.size
            img_rgb = img.convert("RGB")
            image_rgb = np.array(img_rgb)
            
            img_gray = img.convert("L")
            image_gray = np.array(img_gray)
            
            is_jpeg = img.format == "JPEG"
    except Exception as e:
        raise UnsupportedFormatError(f"Cannot process image: {e}")
        
    return IngestionResult(
        sha256=sha256,
        mime_detected=mime_detected,
        extension_declared=extension_declared,
        extension_mismatch=extension_mismatch,
        width=width,
        height=height,
        image_rgb=image_rgb,
        image_gray=image_gray,
        is_jpeg=is_jpeg,
    )
