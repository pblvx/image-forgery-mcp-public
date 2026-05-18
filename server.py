from ..schemas import ForgeryScore
from ..settings import settings

def compute_score(
    ela: float = 0.0,
    noise: float = 0.0,
    blur: float = 0.0,
    jpeg: float = 0.0,
    metadata: float = 0.0,
    edge: float = 0.0,
    resampling: float = 0.0,
    container: float = 0.0,
) -> ForgeryScore:
    """Calculate the final aggregated score and decide the warning level."""
    
    visual_score = (
        ela * settings.score_weight_ela +
        noise * settings.score_weight_noise +
        jpeg * settings.score_weight_jpeg +
        edge * settings.score_weight_edge +
        blur * settings.score_weight_blur +
        resampling * settings.score_weight_resamp
    )
    
    # Metadata contribution
    meta_contribution = min(metadata, settings.score_meta_bonus)
    final = visual_score + meta_contribution
    
    # Cap if there are no visual signals
    if visual_score < 0.1 and metadata > 0:
        final = min(final, settings.score_meta_only_cap)
        
    final = min(1.0, max(0.0, final))
    
    if final >= settings.threshold_manual:
        decision = 'manual_review_required'
    elif final >= settings.threshold_high:
        decision = 'high_suspicion'
    elif final >= settings.threshold_medium:
        decision = 'medium_suspicion'
    else:
        decision = 'low_suspicion'
        
    return ForgeryScore(
        ela_score=ela,
        noise_score=noise,
        jpeg_score=jpeg,
        edge_score=edge,
        blur_score=blur,
        resampling_score=resampling,
        metadata_score=metadata,
        container_score=container,
        final_score=final,
        decision=decision,
    )
