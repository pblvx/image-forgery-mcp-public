import numpy as np

from ..schemas import FusionResult


def fuse_heatmaps(maps: dict[str, np.ndarray]) -> FusionResult:
    """Combine multiple heatmaps into a single visualization."""
    if not maps:
        return FusionResult(
            heatmap=np.zeros((256, 256), dtype=np.uint8),
            visual_score=0.0
        )
        
    shapes = [m.shape for m in maps.values()]
    target_shape = shapes[0]
    
    fused = np.zeros(target_shape, dtype=np.float32)
    weight = 1.0 / len(maps)
    
    for m in maps.values():
        if m.shape != target_shape:
            # Should not happen as all come from same image, but just in case
            import cv2
            m = cv2.resize(m, (target_shape[1], target_shape[0]))
        fused += m.astype(np.float32) * weight
        
    fused_heatmap = np.clip(fused, 0, 255).astype(np.uint8)
    visual_score = min(1.0, float(np.max(fused)) / 255.0)
    
    return FusionResult(
        heatmap=fused_heatmap,
        visual_score=visual_score
    )
