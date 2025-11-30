from image_ops import ImageEditor
from PIL import Image
import os

def create_test_image():
    # Create a simple RGB image
    img = Image.new('RGB', (100, 100), color = 'red')
    return img

def test_ops():
    img = create_test_image()
    print("Testing Image Ops...")
    
    try:
        # Test Exposure
        res = ImageEditor.adjust_exposure(img, 1.5)
        print("Exposure: OK")
    except Exception as e:
        print(f"Exposure Failed: {e}")

    try:
        # Test Highlights
        res = ImageEditor.adjust_highlights(img, 1.5)
        print("Highlights: OK")
    except Exception as e:
        print(f"Highlights Failed: {e}")

    try:
        # Test Vignette
        res = ImageEditor.apply_vignette(img)
        print("Vignette: OK")
    except Exception as e:
        print(f"Vignette Failed: {e}")

    try:
        # Test Warmth
        res = ImageEditor.apply_warmth(img)
        print("Warmth: OK")
    except Exception as e:
        print(f"Warmth Failed: {e}")

    try:
        # Test Cool
        res = ImageEditor.apply_cool(img)
        print("Cool: OK")
    except Exception as e:
        print(f"Cool Failed: {e}")

if __name__ == "__main__":
    test_ops()
