from image_ops import ImageEditor
from PIL import Image
import unittest
import os

class TestImageOps(unittest.TestCase):
    def setUp(self):
        self.img = Image.new('RGB', (100, 100), color='red')
        # Add some pattern to verify transforms
        for i in range(50):
            self.img.putpixel((i, i), (0, 255, 0))

    def test_mirror(self):
        res = ImageEditor.mirror(self.img)
        self.assertEqual(res.size, (100, 100))
        # Check pixel flip
        # Original (0,0) is green. Mirrored (99,0) should be green?
        # Mirror flips left-right.
        # (0,0) -> (99,0)
        self.assertEqual(res.getpixel((99, 0)), (0, 255, 0))

    def test_skew_horizontal(self):
        res = ImageEditor.skew(self.img, 45, 'horizontal')
        # Skew 45 deg horizontal: width increases by height * tan(45) = 100
        # New width should be approx 200
        self.assertTrue(190 < res.width < 210)
        self.assertEqual(res.height, 100)

    def test_skew_vertical(self):
        res = ImageEditor.skew(self.img, 45, 'vertical')
        # Skew 45 deg vertical: height increases
        self.assertEqual(res.width, 100)
        self.assertTrue(190 < res.height < 210)

    def test_perspective(self):
        res = ImageEditor.apply_perspective(self.img, 0.5)
        self.assertEqual(res.size, (100, 100))
        # Hard to test exact pixels without visual inspection, but it should run without error

if __name__ == '__main__':
    unittest.main()
