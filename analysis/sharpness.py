import numpy as np
from PIL import Image

def calculate_sharpness(img):
    """
    Calculate sharpness using Laplacian variance.
    """
    gray = img.convert('L')
    arr = np.array(gray, dtype=np.float32)
    
    # Laplacian Kernel
    # [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
    
    padded = np.pad(arr, ((1, 1), (1, 1)), mode='edge')
    
    # Simple convolution
    top = padded[:-2, 1:-1]
    bottom = padded[2:, 1:-1]
    left = padded[1:-1, :-2]
    right = padded[1:-1, 2:]
    center = padded[1:-1, 1:-1]
    
    laplacian = top + bottom + left + right - 4 * center
    
    variance = np.var(laplacian)
    return variance

def analyze_sharpness(img_orig, img_edited):
    """
    Compare sharpness.
    """
    sharp_orig = calculate_sharpness(img_orig)
    sharp_edited = calculate_sharpness(img_edited)
    
    return {
        "sharpness_original": float(sharp_orig),
        "sharpness_edited": float(sharp_edited),
        "sharpness_delta": float(sharp_edited - sharp_orig)
    }
