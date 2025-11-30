import numpy as np
from PIL import Image
import math

def calculate_mse(img1, img2):
    """Calculate Mean Squared Error"""
    arr1 = np.array(img1, dtype=np.float32)
    arr2 = np.array(img2, dtype=np.float32)
    mse = np.mean((arr1 - arr2) ** 2)
    return mse

def calculate_psnr(img1, img2):
    """Calculate Peak Signal-to-Noise Ratio"""
    mse = calculate_mse(img1, img2)
    if mse == 0:
        return float('inf')
    max_pixel = 255.0
    psnr = 20 * math.log10(max_pixel / math.sqrt(mse))
    return psnr

def calculate_snr(img):
    """Calculate Signal-to-Noise Ratio"""
    arr = np.array(img, dtype=np.float32)
    mean_signal = np.mean(arr)
    std_noise = np.std(arr)
    if std_noise == 0:
        return float('inf')
    snr = 20 * math.log10(mean_signal / std_noise)
    return snr

def calculate_entropy(img):
    """Calculate Image Entropy"""
    gray = img.convert('L')
    histogram = gray.histogram()
    histogram_length = sum(histogram)
    samples_probability = [float(h) / histogram_length for h in histogram]
    entropy = -sum([p * math.log(p, 2) for p in samples_probability if p != 0])
    return entropy

def calculate_ssim(img1, img2):
    """
    Calculate Structural Similarity Index (SSIM) - Simplified Numpy Implementation
    Based on Wang et al. (2004)
    """
    # Convert to grayscale for SSIM
    i1 = np.array(img1.convert('L'), dtype=np.float32)
    i2 = np.array(img2.convert('L'), dtype=np.float32)
    
    # Constants
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    
    # Mean
    mu1 = np.mean(i1)
    mu2 = np.mean(i2)
    
    # Variance
    sigma1_sq = np.var(i1)
    sigma2_sq = np.var(i2)
    
    # Covariance
    sigma12 = np.mean((i1 - mu1) * (i2 - mu2))
    
    # SSIM Formula
    num = (2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)
    den = (mu1**2 + mu2**2 + c1) * (sigma1_sq + sigma2_sq + c2)
    
    return num / den

def analyze_metrics(img_orig, img_edited):
    """Run all metrics"""
    # Ensure same size for comparison
    if img_orig.size != img_edited.size:
        img_edited_resized = img_edited.resize(img_orig.size)
    else:
        img_edited_resized = img_edited
        
    mse = calculate_mse(img_orig, img_edited_resized)
    psnr = calculate_psnr(img_orig, img_edited_resized)
    ssim = calculate_ssim(img_orig, img_edited_resized)
    
    snr_orig = calculate_snr(img_orig)
    snr_edit = calculate_snr(img_edited)
    
    entropy_orig = calculate_entropy(img_orig)
    entropy_edit = calculate_entropy(img_edited)
    
    return {
        "mse": mse,
        "psnr": psnr,
        "ssim": ssim,
        "snr_orig": snr_orig,
        "snr_edit": snr_edit,
        "entropy_orig": entropy_orig,
        "entropy_edit": entropy_edit
    }
