#!/usr/bin/env python3
"""Test the new histogram visualization"""
import sys
sys.path.insert(0, r'c:\Users\Pratham B\Python Project\pypic_editor')

from PIL import Image
from analysis import histogram
import numpy as np

print("Testing histogram visualization...")

# Create test images
print("Creating test images...")
img_orig = Image.new('RGB', (100, 100))
pixels_orig = img_orig.load()
for i in range(100):
    for j in range(100):
        pixels_orig[i, j] = (i * 2, j * 2, 128)

img_edited = Image.new('RGB', (100, 100))
pixels_edited = img_edited.load()
for i in range(100):
    for j in range(100):
        pixels_edited[i, j] = (min(255, i * 2 + 50), j * 2, 100)

print("Running histogram analysis...")
result = histogram.analyze_histogram(img_orig, img_edited)

print(f"Brightness delta: {result['brightness_delta']:.2f}")
print(f"Contrast delta: {result['contrast_delta']:.2f}")
print(f"Histogram delta score: {result['histogram_delta_score']:.2f}%")

print(f"\nPlot sizes:")
print(f"Original: {result['plot_original'].size}")
print(f"Edited: {result['plot_edited'].size}")
print(f"Difference: {result['plot_diff'].size}")

print("\nSaving test plots...")
result['plot_original'].save('test_hist_orig.png')
result['plot_edited'].save('test_hist_edit.png')
result['plot_diff'].save('test_hist_diff.png')

print("✓ Test complete! Check test_hist_*.png files")
