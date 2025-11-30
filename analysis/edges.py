import numpy as np
from PIL import Image
from utils import ensure_rgb, normalize_array

def sobel_edge_detection(img):
    """
    Apply Sobel edge detection.
    Returns: (magnitude_map_image, edge_density_score)
    """
    # Convert to grayscale for edge detection
    gray = img.convert('L')
    img_arr = np.array(gray, dtype=np.float32)

    # Sobel Kernels
    Gx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    Gy = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)

    # Convolve (using simple slicing for 3x3 kernel to avoid heavy scipy dependency if possible, 
    # but for robustness/speed on larger images, manual implementation is fine for this scope)
    # We'll implement a simple convolution helper or use manual sliding for clarity.
    
    rows, cols = img_arr.shape
    
    # Pad image to handle borders
    padded = np.pad(img_arr, ((1, 1), (1, 1)), mode='edge')
    
    # Vectorized sliding windows would be faster, but let's do a reasonably efficient manual approach
    # or use simple shifting for 3x3
    
    # Efficient 3x3 convolution using shifting
    # Top row
    tl = padded[:-2, :-2]
    tc = padded[:-2, 1:-1]
    tr = padded[:-2, 2:]
    # Middle row
    ml = padded[1:-1, :-2]
    # mc = padded[1:-1, 1:-1] # center not used in Sobel
    mr = padded[1:-1, 2:]
    # Bottom row
    bl = padded[2:, :-2]
    bc = padded[2:, 1:-1]
    br = padded[2:, 2:]

    # Gx = (tr + 2*mr + br) - (tl + 2*ml + bl)
    grad_x = (tr + 2*mr + br) - (tl + 2*ml + bl)
    
    # Gy = (bl + 2*bc + br) - (tl + 2*tc + tr)
    grad_y = (bl + 2*bc + br) - (tl + 2*tc + tr)

    magnitude = np.sqrt(grad_x**2 + grad_y**2)
    
    # Normalize for display
    mag_norm = normalize_array(magnitude)
    edge_img = Image.fromarray(mag_norm, mode='L')
    
    # Density: fraction of pixels > 80 (approx 30% of 255)
    threshold = 80
    density = np.mean(mag_norm > threshold)
    
    return edge_img, density, mag_norm

def analyze_edges(img_orig, img_edited):
    """
    Perform full edge analysis.
    """
    orig_edge_img, orig_density, orig_mag = sobel_edge_detection(img_orig)
    edited_edge_img, edited_density, edited_mag = sobel_edge_detection(img_edited)
    
    # Difference Map
    # Green = New edges (Edited > Orig)
    # Red = Lost edges (Orig > Edited)
    
    diff_h = orig_mag.shape[0]
    diff_w = orig_mag.shape[1]
    diff_map = np.zeros((diff_h, diff_w, 3), dtype=np.uint8)
    
    # Threshold for significant difference to reduce noise
    diff_threshold = 20
    
    diff = edited_mag.astype(np.float32) - orig_mag.astype(np.float32)
    
    # New edges (Positive diff) -> Green
    mask_new = diff > diff_threshold
    diff_map[mask_new, 1] = np.clip(diff[mask_new], 0, 255) # Green channel
    
    # Lost edges (Negative diff) -> Red
    mask_lost = diff < -diff_threshold
    diff_map[mask_lost, 0] = np.clip(-diff[mask_lost], 0, 255) # Red channel
    
    diff_img = Image.fromarray(diff_map, mode='RGB')
    
    return {
        "orig_edge": orig_edge_img,
        "edited_edge": edited_edge_img,
        "difference_map": diff_img,
        "density_original": float(orig_density),
        "density_edited": float(edited_density),
        "density_delta": float(edited_density - orig_density),
        "preservation_score": calculate_edge_preservation(orig_mag, edited_mag)
    }

def laplacian_edge_detection(img):
    """Laplacian Edge Detection"""
    gray = img.convert('L')
    arr = np.array(gray, dtype=np.float32)
    # Simple 3x3 Laplacian
    # [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
    padded = np.pad(arr, ((1, 1), (1, 1)), mode='edge')
    lap = padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:] - 4 * padded[1:-1, 1:-1]
    return normalize_array(np.abs(lap))

def calculate_edge_preservation(orig_mag, edit_mag):
    """
    Calculate Edge Preservation Score.
    Correlation between edge magnitudes.
    """
    # Flatten
    f1 = orig_mag.flatten()
    f2 = edit_mag.flatten()
    
    # Correlation coefficient
    if np.std(f1) == 0 or np.std(f2) == 0:
        return 0.0
    
    corr = np.corrcoef(f1, f2)[0, 1]
    return corr
