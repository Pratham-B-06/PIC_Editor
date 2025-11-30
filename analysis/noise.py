import numpy as np
from PIL import Image
from utils import normalize_array

def calculate_local_variance(img):
    """
    Calculate 3x3 local variance for noise estimation.
    Returns: (variance_map_image, heatmap_image, mean_variance, variance_array)
    """
    gray = img.convert('L')
    arr = np.array(gray, dtype=np.float32)
    
    # Pad for 3x3 window
    padded = np.pad(arr, ((1, 1), (1, 1)), mode='reflect')
    
    # Collect all 9 neighbors
    neighbors = []
    for i in range(3):
        for j in range(3):
            neighbors.append(padded[i:i+arr.shape[0], j:j+arr.shape[1]])
            
    stack = np.stack(neighbors, axis=0)
    
    # Calculate variance along the stack axis (axis 0)
    local_var = np.var(stack, axis=0)
    
    mean_var = np.mean(local_var)
    
    # Normalize variance for visualization
    var_norm = normalize_array(local_var)
    
    # Create Heatmap
    # High noise (yellow) = (255, 255, 0)
    # Low noise (blue) = (0, 0, 255)
    
    heatmap = np.zeros((arr.shape[0], arr.shape[1], 3), dtype=np.uint8)
    
    heatmap[:, :, 0] = var_norm # R
    heatmap[:, :, 1] = var_norm # G
    heatmap[:, :, 2] = 255 - var_norm # B
    
    return Image.fromarray(var_norm, 'L'), Image.fromarray(heatmap, 'RGB'), mean_var, local_var

def estimate_gaussian_noise(img):
    """
    Estimate Gaussian noise standard deviation.
    """
    gray = img.convert('L')
    arr = np.array(gray, dtype=np.float32)
    
    h, w = arr.shape
    if h < 3 or w < 3: return 0.0
    
    padded = np.pad(arr, ((1, 1), (1, 1)), mode='edge')
    
    # Convolve with Laplacian-like kernel
    # [[1, -2, 1], [-2, 4, -2], [1, -2, 1]]
    conv = (
        1*padded[:-2, :-2] + -2*padded[:-2, 1:-1] + 1*padded[:-2, 2:] +
        -2*padded[1:-1, :-2] + 4*padded[1:-1, 1:-1] + -2*padded[1:-1, 2:] +
        1*padded[2:, :-2] + -2*padded[2:, 1:-1] + 1*padded[2:, 2:]
    )
    
    # sigma = std(conv) / 6.0
    sigma = np.std(conv) / 6.0
    return sigma

def analyze_noise(img_orig, img_edited):
    """
    Perform full noise analysis.
    """
    orig_map, orig_heat, orig_score, orig_var_arr = calculate_local_variance(img_orig)
    edited_map, edited_heat, edited_score, edited_var_arr = calculate_local_variance(img_edited)
    
    # Difference Map
    diff_map = np.zeros((orig_var_arr.shape[0], orig_var_arr.shape[1], 3), dtype=np.uint8)
    diff = edited_var_arr - orig_var_arr
    
    threshold = 5.0 # Variance threshold
    
    # Noise Increased -> Green (Positive diff)
    mask_inc = diff > threshold
    diff_map[mask_inc, 1] = 255 
    
    # Noise Decreased -> Red (Negative diff)
    mask_dec = diff < -threshold
    diff_map[mask_dec, 0] = 255
    
    diff_img = Image.fromarray(diff_map, 'RGB')
    
    # Gaussian estimates
    gauss_orig = estimate_gaussian_noise(img_orig)
    gauss_edit = estimate_gaussian_noise(img_edited)
    
    return {
        "original_noise_map": orig_map,
        "edited_noise_map": edited_map,
        "original_heatmap": orig_heat,
        "edited_heatmap": edited_heat,
        "difference_map": diff_img,
        "noise_original": float(orig_score),
        "noise_edited": float(edited_score),
        "noise_delta": float(edited_score - orig_score),
        "gaussian_noise_orig": float(gauss_orig),
        "gaussian_noise_edit": float(gauss_edit)
    }
