"""
Button and Slider Test Script
This script tests if all major components can be imported and instantiated.
"""

print("Testing imports...")

try:
    from PIL import Image, ImageTk
    print("✓ PIL imports OK")
except Exception as e:
    print(f"✗ PIL import failed: {e}")

try:
    import tkinter as tk
    from tkinter import ttk
    print("✓ Tkinter imports OK")
except Exception as e:
    print(f"✗ Tkinter import failed: {e}")

try:
    from image_ops import ImageEditor
    print("✓ ImageEditor import OK")
except Exception as e:
    print(f"✗ ImageEditor import failed: {e}")

try:
    from transform_tools import create_transform_tools
    print("✓ Transform tools import OK")
except Exception as e:
    print(f"✗ Transform tools import failed: {e}")

try:
    from analysis import edges, noise, histogram, sharpness, report, metrics, artifacts
    print("✓ Analysis modules import OK")
except Exception as e:
    print(f"✗ Analysis modules import failed: {e}")

print("\nTesting ImageEditor methods...")
test_img = Image.new('RGB', (100, 100), color='red')

methods_to_test = [
    ('adjust_brightness', [test_img, 1.5]),
    ('adjust_contrast', [test_img, 1.5]),
    ('rotate', [test_img, 45]),
    ('rotate', [test_img, 45]),
    ('to_grayscale', [test_img]),
    ('blur', [test_img]),
    ('sharpen', [test_img]),
]

for method_name, args in methods_to_test:
    try:
        method = getattr(ImageEditor, method_name)
        result = method(*args)
        print(f"✓ {method_name} OK")
    except Exception as e:
        print(f"✗ {method_name} failed: {e}")

print("\nAll tests complete!")
