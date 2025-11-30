import numpy as np
from PIL import Image

def detect_compression_artifacts(img):
    """
    Estimate compression artifacts (blockiness).
    """
    gray = img.convert('L')
    arr = np.array(gray, dtype=np.float32)
    
    # Check for 8x8 block boundaries
    # Calculate differences at 8-pixel intervals
    
    h, w = arr.shape
    
    # Horizontal boundaries
    diff_h = np.abs(arr[:, 7:w-1:8] - arr[:, 8:w:8])
    # Vertical boundaries
    diff_v = np.abs(arr[7:h-1:8, :] - arr[8:h:8, :])
    
    # Non-boundary differences for normalization
    diff_h_non = np.abs(arr[:, 3:w-5:8] - arr[:, 4:w-4:8])
    diff_v_non = np.abs(arr[3:h-5:8, :] - arr[4:h-4:8, :])
    
    score_h = np.mean(diff_h) - np.mean(diff_h_non)
    score_v = np.mean(diff_v) - np.mean(diff_v_non)
    
    # Positive score indicates blockiness
    score = max(0, score_h + score_v)
    return score

def detect_oversmoothing(img):
    """
    Detect oversmoothing (lack of texture).
    """
    gray = img.convert('L')
    arr = np.array(gray, dtype=np.float32)
    
    # Calculate local variance
    # Low variance everywhere = oversmoothed
    
    # We can use Laplacian variance as a proxy for texture
    from analysis.sharpness import calculate_sharpness
    
    score = calculate_sharpness(img)
    # Lower score = more smooth
    return score
