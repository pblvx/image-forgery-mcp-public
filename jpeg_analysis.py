import numpy as np
import cv2

from ..schemas import CopyMoveResult


def analyze_copy_move(image_gray: np.ndarray) -> CopyMoveResult:
    """Detect copy-move forgery using ORB keypoint matching."""
    orb = cv2.ORB_create(nfeatures=1000)  # type: ignore
    keypoints, descriptors = orb.detectAndCompute(image_gray, None)
    
    score = 0.0
    limitations = [
        "Copy-move computacionalmente costoso, puede dar falsos positivos en patrones repetitivos naturales."
    ]
    
    if descriptors is not None and len(descriptors) > 10:
        # Use Brute Force Matcher with Hamming distance for ORB
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        # Find 2 nearest neighbors
        matches = bf.knnMatch(descriptors, descriptors, k=2)
        
        good_matches = []
        for match_pair in matches:
            if len(match_pair) < 2:
                continue
            m, n = match_pair
            # We want to find matches that are not the exact same keypoint
            # So distance should be strictly greater than 0 ideally, or we check pt distance
            pt1 = keypoints[m.queryIdx].pt
            pt2 = keypoints[m.trainIdx].pt
            dist = np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
            
            # If distance is large enough, and ratio test passes (similar descriptors)
            if dist > 30.0 and m.distance < 0.75 * n.distance:
                good_matches.append(m)
                
        # If we have enough good matches, we might have copy-move
        if len(good_matches) > 5:
            score = min(1.0, len(good_matches) / 50.0)

    return CopyMoveResult(
        copy_move_score=score,
        limitations=limitations
    )
