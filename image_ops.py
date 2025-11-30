from PIL import Image, ImageEnhance, ImageFilter, ImageOps

class ImageEditor:
    @staticmethod
    def adjust_brightness(img, factor):
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)

    @staticmethod
    def adjust_contrast(img, factor):
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)

    @staticmethod
    def rotate(img, angle):
        return img.rotate(angle, expand=True)

    @staticmethod
    def crop(img, box):
        # box = (left, top, right, bottom)
        return img.crop(box)

    @staticmethod
    def resize(img, size):
        return img.resize(size, Image.Resampling.LANCZOS)

    @staticmethod
    def to_grayscale(img):
        return ImageOps.grayscale(img).convert("RGB")

    @staticmethod
    def apply_sepia(img):
        # Sepia matrix
        sepia_filter = (0.393, 0.769, 0.189, 0,
                        0.349, 0.686, 0.168, 0,
                        0.272, 0.534, 0.131, 0)
        img = img.convert("RGB")
        # Apply matrix
        # PIL convert allows matrix but it's for RGB -> RGB
        # We can use color matrix
        # Or manually:
        # R = Tr * 0.393 + Tg * 0.769 + Tb * 0.189
        # etc.
        # Easier way using PIL internal matrix conversion:
        return img.convert("RGB", matrix=sepia_filter)

    @staticmethod
    def blur(img, radius=2):
        return img.filter(ImageFilter.GaussianBlur(radius))

    @staticmethod
    def sharpen(img):
        return img.filter(ImageFilter.SHARPEN)

    @staticmethod
    def apply_emboss(img):
        return img.filter(ImageFilter.EMBOSS)

    @staticmethod
    def adjust_highlights(img, factor):
        # factor: 0.5 to 2.0
        # We want to affect pixels > 128
        # If factor > 1, we brighten highlights
        # If factor < 1, we darken highlights
        
        # Create a lookup table
        lut = []
        for i in range(256):
            if i <= 128:
                lut.append(i)
            else:
                # Scale the part above 128
                delta = i - 128
                new_delta = delta * factor
                new_val = 128 + new_delta
                lut.append(int(min(255, max(0, new_val))))
        
        if img.mode == 'RGB':
            lut = lut * 3
        
        return img.point(lut)
            
    @staticmethod
    def adjust_exposure(img, factor):
        # Simple exposure adjustment (similar to brightness but often gamma based)
        # For simplicity, we'll use brightness enhancement for now
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)

    @staticmethod
    def apply_vignette(img, intensity=0.5):
        if img.mode != 'RGB':
            img = img.convert('RGB')
        width, height = img.size
        
        # Create a gradient mask
        # Center is white (opaque), edges are black (transparent) -> wait, for vignette we want edges dark.
        # So we want a mask that is white at center and black at edges, then multiply?
        # Or create a black layer and use the mask to composite.
        
        # Let's create a radial gradient
        # This is a bit complex to do purely with PIL efficiently without numpy, but let's try a simple way.
        # Or just return original for now if too complex, but let's try.
        
        # Placeholder implementation: just return image for now to avoid complexity in this step
        # Real implementation would require creating a radial gradient mask.
        return img

    @staticmethod
    def adjust_exposure(img, factor):
        # Exposure is effectively brightness multiplier
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)

    @staticmethod
    def apply_vignette(img, intensity=0.5):
        # Create a gradient mask
        width, height = img.size
        # Create a radial gradient
        # We can use ImageOps.colorize or manual creation
        # Simple way: Create a radial gradient image
        
        # Create a mask layer
        mask = Image.new('L', (width, height), 255)
        
        # We need a radial gradient. 
        # Let's use a simple distance calculation or a pre-made radial image if possible.
        # Efficient way:
        import math
        
        # Create a radial gradient
        # Center
        cx, cy = width / 2, height / 2
        max_dist = math.sqrt(cx**2 + cy**2)
        
        # This is slow in pure python for large images.
        # Better: Use a radial gradient image created via drawing
        from PIL import ImageDraw
        
        # Create a radial gradient using draw
        # Draw a large circle
        # Actually, let's just darken corners.
        
        # Fast approximation:
        # Create a smaller gradient and resize it
        g_width, g_height = 256, 256
        gradient = Image.new('L', (g_width, g_height), 0)
        draw = ImageDraw.Draw(gradient)
        
        # Draw concentric circles
        center_x, center_y = g_width // 2, g_height // 2
        radius = max(center_x, center_y)
        
        for r in range(radius, 0, -1):
            # Calculate alpha based on distance
            # Center is white (transparent), edges are black (opaque)
            # We want mask: Center=255 (keep), Edges=0 (darken)
            
            # Normalized distance from center (0 to 1)
            dist = r / radius
            # Falloff function
            val = int(255 * (1 - dist**2)) # Quadratic falloff
            draw.ellipse((center_x - r, center_y - r, center_x + r, center_y + r), fill=val)
            
        # Resize gradient to image size
        mask = gradient.resize((width, height), Image.Resampling.LANCZOS)
        
        # Composite
        # Create black image
        black = Image.new('RGB', (width, height), (0, 0, 0))
        
        # Blend original and black using mask
        # Where mask is 255, we want original. Where 0, we want black.
        return Image.composite(img, black, mask)

    @staticmethod
    def apply_warmth(img):
        # Increase Red, Decrease Blue
        r, g, b = img.split()
        r = r.point(lambda i: i * 1.1)
        b = b.point(lambda i: i * 0.9)
        return Image.merge('RGB', (r, g, b))

    @staticmethod
    def apply_cool(img):
        # Increase Blue, Decrease Red
        r, g, b = img.split()
        r = r.point(lambda i: i * 0.9)
        b = b.point(lambda i: i * 1.1)
        return Image.merge('RGB', (r, g, b))


    @staticmethod
    def skew(img, angle, direction='horizontal'):
        # Skew using affine transform
        # angle is in degrees
        import math
        
        # Convert angle to radians
        # Limit angle to avoid extreme distortion
        angle = max(-45, min(45, angle))
        rad = math.radians(angle)
        tan_theta = math.tan(rad)
        
        width, height = img.size
        
        if direction == 'horizontal':
            # x' = x + y * tan(theta)
            # y' = y
            m = (1, tan_theta, 0, 0, 1, 0)
            new_width = width + int(abs(height * tan_theta))
            return img.transform((new_width, height), Image.AFFINE, m, Image.Resampling.BICUBIC)
        else:
            # x' = x
            # y' = y + x * tan(theta)
            m = (1, 0, 0, tan_theta, 1, 0)
            new_height = height + int(abs(width * tan_theta))
            return img.transform((width, new_height), Image.AFFINE, m, Image.Resampling.BICUBIC)


