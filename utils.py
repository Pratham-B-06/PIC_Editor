import numpy as np
from PIL import Image, ImageTk

def pil_to_tk(img, max_size=(320, 320)):
    """
    Convert a PIL Image to a Tkinter-compatible PhotoImage, 
    resizing it to fit within max_size while maintaining aspect ratio.
    """
    img_copy = img.copy()
    img_copy.thumbnail(max_size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img_copy)

def ensure_rgb(img):
    """Ensure image is in RGB mode."""
    if img.mode != 'RGB':
        return img.convert('RGB')
    return img

def normalize_array(arr):
    """Normalize a numpy array to 0-255 range for image display."""
    arr_min = arr.min()
    arr_max = arr.max()
    if arr_max - arr_min == 0:
        return np.zeros_like(arr, dtype=np.uint8)
    
    norm = (arr - arr_min) / (arr_max - arr_min) * 255
    return norm.astype(np.uint8)
