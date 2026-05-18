import numpy as np
import cv2

from ..schemas import NoiseResult
from ..settings import settings


def analyze_noise(image_gray: np.ndarray) -> NoiseResult:
    """Analyze noise inconsistency in the image using a Wiener-like or Median filter approach."""
    block_size = settings.noise_block_size
    sigma_thresh = settings.noise_threshold_sigma
    
    # Extract noise residual using a median filter
    filtered = cv2.medianBlur(image_gray, 3)
    residual = np.abs(image_gray.astype(np.float32) - filtered.astype(np.float32))
    
    h, w = residual.shape
    regions = []
    block_vars = []
    
    for y in range(0, h - block_size + 1, block_size):
        for x in range(0, w - block_size + 1, block_size):
            block = residual[y:y+block_size, x:x+block_size]
            var_val = float(np.var(block))
            block_vars.append(var_val)
            
    if block_vars:
        global_mean = float(np.mean(block_vars))
        global_std = float(np.std(block_vars))
        
        for y in range(0, h - block_size + 1, block_size):
            for x in range(0, w - block_size + 1, block_size):
                block = residual[y:y+block_size, x:x+block_size]
                var_val = float(np.var(block))
                if global_std > 0:
                    z_score = float(abs(var_val - global_mean) / global_std)
                    if z_score > sigma_thresh:
                        score = float(min(1.0, z_score / 10.0))
                        regions.append((x, y, block_size, block_size, score))
                        
        noise_score = 0.0
        if regions:
            noise_score = float(min(1.0, len(regions) / (len(block_vars) * 0.1)))
            max_region_score = float(max(r[4] for r in regions))
            noise_score = float(max(noise_score, max_region_score))
    else:
        noise_score = 0.0

    return NoiseResult(
        noise_map=residual.astype(np.uint8),
        noise_score=noise_score,
        anomalous_regions=regions,
        limitations=[
            "El ruido puede verse afectado por una fuerte compresión JPEG."
        ]
    )
