import numpy as np
import cv2

from ..schemas import SharpnessResult
from ..settings import settings


def analyze_sharpness(image_gray: np.ndarray) -> SharpnessResult:
    """Analyze sharpness inconsistency by computing local Laplacian variance."""
    block_size = settings.sharp_block_size
    sigma_thresh = settings.sharp_anomaly_sigma
    
    # Compute the Laplacian
    laplacian = cv2.Laplacian(image_gray, cv2.CV_64F)
    sharpness_map = np.abs(laplacian).astype(np.float32)
    
    h, w = sharpness_map.shape
    regions = []
    block_vars = []
    
    for y in range(0, h - block_size + 1, block_size):
        for x in range(0, w - block_size + 1, block_size):
            block = sharpness_map[y:y+block_size, x:x+block_size]
            var_val = float(np.var(block))
            block_vars.append(var_val)
            
    if block_vars:
        global_mean = float(np.mean(block_vars))
        global_std = float(np.std(block_vars))
        
        for y in range(0, h - block_size + 1, block_size):
            for x in range(0, w - block_size + 1, block_size):
                block = sharpness_map[y:y+block_size, x:x+block_size]
                var_val = float(np.var(block))
                if global_std > 0:
                    z_score = float(abs(var_val - global_mean) / global_std)
                    if z_score > sigma_thresh:
                        score = float(min(1.0, z_score / 10.0))
                        regions.append((x, y, block_size, block_size, score))
                        
        blur_score = 0.0
        sharp_anomaly_score = 0.0
        if regions:
            sharp_anomaly_score = float(min(1.0, len(regions) / (len(block_vars) * 0.1)))
            max_region_score = float(max(r[4] for r in regions))
            blur_score = float(max(sharp_anomaly_score, max_region_score))
    else:
        blur_score = 0.0
        sharp_anomaly_score = 0.0

    return SharpnessResult(
        sharpness_map=np.clip(sharpness_map, 0, 255).astype(np.uint8),
        blur_score=blur_score,
        sharp_anomaly_score=sharp_anomaly_score,
        anomalous_regions=regions,
        limitations=[
            "El desenfoque natural (profundidad de campo) puede causar falsos positivos."
        ]
    )
