import io
import numpy as np
from PIL import Image

from ..schemas import ELAResult
from ..settings import settings

def compute_ela(image_rgb: np.ndarray) -> ELAResult:
    """Compute Error Level Analysis on the image."""
    quality = settings.ela_quality
    amplify = settings.ela_amplify
    block_size = settings.ela_region_block
    sigma_thresh = settings.ela_region_sigma
    
    pil_img = Image.fromarray(image_rgb)
    buf = io.BytesIO()
    pil_img.save(buf, format='JPEG', quality=quality)
    buf.seek(0)
    recompressed = Image.open(buf).convert('RGB')
    recomp_arr = np.array(recompressed).astype(np.float32)
    
    orig_arr = image_rgb.astype(np.float32)
    diff = np.abs(orig_arr - recomp_arr)
    
    ela_amplified = np.clip(diff * amplify, 0, 255).astype(np.uint8)
    ela_gray = np.mean(ela_amplified, axis=2)
    
    h, w = ela_gray.shape
    regions = []
    block_means = []
    
    for y in range(0, h - block_size + 1, block_size):
        for x in range(0, w - block_size + 1, block_size):
            block = ela_gray[y:y+block_size, x:x+block_size]
            mean_val = np.mean(block)
            block_means.append(mean_val)
            
    if block_means:
        global_mean = float(np.mean(block_means))
        global_std = float(np.std(block_means))
        
        for y in range(0, h - block_size + 1, block_size):
            for x in range(0, w - block_size + 1, block_size):
                block = ela_gray[y:y+block_size, x:x+block_size]
                mean_val = float(np.mean(block))
                if global_std > 0:
                    z_score = (mean_val - global_mean) / global_std
                    if z_score > sigma_thresh:
                        score = min(1.0, z_score / 10.0)
                        regions.append((x, y, block_size, block_size, score))
                        
        ela_score = min(1.0, max(0.0, (global_mean / 255.0) * 2.0))
        # If there are highly anomalous regions, increase the score
        if regions:
            max_region_score = max(r[4] for r in regions)
            ela_score = max(ela_score, max_region_score)
    else:
        ela_score = 0.0

    return ELAResult(
        ela_image=ela_amplified,
        ela_score=ela_score,
        anomalous_regions=regions,
        limitations=[
            "ELA poco fiable en imágenes muy recomprimidas (mensajería, escáneres).",
            "Imágenes con fondo uniforme pueden generar falsos positivos."
        ]
    )
