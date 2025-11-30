import numpy as np
from PIL import Image, ImageDraw, ImageFont

def calculate_histogram_stats(img):
    """
    Calculate histogram, brightness, and contrast.
    """
    # Ensure RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')
        
    arr = np.array(img)
    
    # Histogram per channel
    hist_r, _ = np.histogram(arr[:,:,0], bins=256, range=(0,256))
    hist_g, _ = np.histogram(arr[:,:,1], bins=256, range=(0,256))
    hist_b, _ = np.histogram(arr[:,:,2], bins=256, range=(0,256))
    
    hist_combined = np.stack([hist_r, hist_g, hist_b])
    
    # Brightness: Mean pixel value
    brightness = np.mean(arr)
    
    # Contrast: Standard deviation of pixel values
    contrast = np.std(arr)
    
    return hist_combined, brightness, contrast

def analyze_histogram(img_orig, img_edited):
    """
    Compare histograms and color stats.
    """
    hist_orig, brit_orig, cont_orig = calculate_histogram_stats(img_orig)
    hist_edited, brit_edited, cont_edited = calculate_histogram_stats(img_edited)
    
    # Histogram Delta Score: Sum of absolute differences normalized
    total_pixels = img_orig.width * img_orig.height
    hist_diff = np.sum(np.abs(hist_orig - hist_edited))
    hist_delta_score = (hist_diff / (total_pixels * 3)) * 100 # Percentage
    
    # Generate Plots with aligned axes
    plot_orig, plot_edit, plot_diff = plot_aligned_histograms_pil(hist_orig, hist_edited)
    
    # Create combined image for export
    plot_combined = create_combined_histogram(plot_orig, plot_edit, plot_diff)
    
    return {
        "hist_original": hist_orig,
        "hist_edited": hist_edited,
        "brightness_delta": float(brit_edited - brit_orig),
        "contrast_delta": float(cont_edited - cont_orig),
        "histogram_delta_score": float(hist_delta_score),
        "plot_original": plot_orig,
        "plot_edited": plot_edit,
        "plot_diff": plot_diff,
        "plot_combined": plot_combined  # Combined vertical image
    }

def create_combined_histogram(plot_orig, plot_edit, plot_diff):
    """
    Combine three histogram plots into a single vertical image.
    All plots are aligned with the same X-axis origin.
    """
    # Get dimensions
    width = plot_orig.width
    height_per_plot = plot_orig.height
    total_height = height_per_plot * 3
    
    # Create combined image
    combined = Image.new('RGB', (width, total_height), (42, 42, 42))
    
    # Paste plots vertically
    combined.paste(plot_orig, (0, 0))
    combined.paste(plot_edit, (0, height_per_plot))
    combined.paste(plot_diff, (0, height_per_plot * 2))
    
    return combined

def smooth_histogram(hist, window=3):
    """Simple moving average smoothing"""
    if window < 2:
        return hist
    smoothed = np.copy(hist).astype(float)
    for i in range(len(hist)):
        start = max(0, i - window // 2)
        end = min(len(hist), i + window // 2 + 1)
        smoothed[i] = np.mean(hist[start:end])
    return smoothed

def plot_aligned_histograms_pil(hist_orig, hist_edited, width=340, height=100):
    """
    Generate three aligned histogram plots using PIL:
    1. Original image histogram
    2. Edited image histogram  
    3. Difference histogram
    
    All plots share the same X-axis (0-255) and Y-axis scale.
    Uses PIL ImageDraw to create professional-looking aligned plots.
    """
    # Apply smoothing
    hist_orig_smooth = np.zeros_like(hist_orig).astype(float)
    hist_edited_smooth = np.zeros_like(hist_edited).astype(float)
    for ch in range(3):
        hist_orig_smooth[ch] = smooth_histogram(hist_orig[ch], window=3)
        hist_edited_smooth[ch] = smooth_histogram(hist_edited[ch], window=3)
    
    # Calculate difference
    hist_diff = hist_edited_smooth - hist_orig_smooth
    
    # Find global Y-max for consistent scaling
    y_max = max(
        np.max(hist_orig_smooth),
        np.max(hist_edited_smooth),
        np.max(np.abs(hist_diff))
    )
    y_max = y_max * 1.1  # 10% padding
    
    # Colors and settings
    colors = [(255, 80, 80), (80, 255, 80), (80, 80, 255)]  # R, G, B
    bg_color = (42, 42, 42)  # #2a2a2a
    text_color = (230, 230, 230)  # #e6e6e6
    grid_color = (64, 64, 64)  # #404040
    
    # Margins for axes
    margin_left = 40
    margin_right = 10
    margin_top = 25
    margin_bottom = 25
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    
    def create_plot(hist_data, title, is_difference=False):
        """Helper to create a single histogram plot"""
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Draw title
        try:
            font_title = ImageFont.truetype("arial.ttf", 10)
            font_label = ImageFont.truetype("arial.ttf", 8)
        except:
            font_title = ImageFont.load_default()
            font_label = ImageFont.load_default()
        
        draw.text((width // 2, 5), title, fill=text_color, font=font_title, anchor="mt")
        
        # Draw axes
        # Y-axis
        draw.line([(margin_left, margin_top), (margin_left, height - margin_bottom)], 
                 fill=grid_color, width=1)
        # X-axis  
        x_axis_y = height - margin_bottom if not is_difference else (margin_top + plot_height // 2)
        draw.line([(margin_left, x_axis_y), (width - margin_right, x_axis_y)], 
                 fill=grid_color, width=1)
        
        # Draw gridlines (vertical every 64 units = 4 lines)
        for x_val in [0, 64, 128, 192, 255]:
            x_px = margin_left + int((x_val / 255.0) * plot_width)
            draw.line([(x_px, margin_top), (x_px, height - margin_bottom)], 
                     fill=(grid_color[0]//2, grid_color[1]//2, grid_color[2]//2), width=1)
            # X-axis labels
            draw.text((x_px, height - margin_bottom + 5), str(x_val), 
                     fill=text_color, font=font_label, anchor="mt")
        
        # Y-axis label
        draw.text((5, margin_top), "Freq", fill=text_color, font=font_label, anchor="lt")
        
        # PlotEach channel
        for ch in range(3):
            points = []
            for x in range(256):
                x_px = margin_left + int((x / 255.0) * plot_width)
                
                if is_difference:
                    # Center around middle for difference
                    val = hist_data[ch, x]
                    y_offset = -int((val / y_max) * (plot_height / 2))
                    y_px = (margin_top + plot_height // 2) + y_offset
                else:
                    # Normal histogram from bottom
                    val = hist_data[ch, x]
                    y_offset = int((val / y_max) * plot_height)
                    y_px = (height - margin_bottom) - y_offset
                
                points.append((x_px, y_px))
            
            # Draw with transparency
            for i in range(len(points) - 1):
                draw.line([points[i], points[i + 1]], 
                         fill=colors[ch] + (180,), width=2)  # Alpha = 180/255 ≈ 0.7
        
        # Draw legend
        legend_x = width - margin_right - 60
        legend_y = margin_top + 5
        labels = ['R', 'G', 'B']
        for i, (color, label) in enumerate(zip(colors, labels)):
            y = legend_y + i * 12
            draw.rectangle([legend_x, y, legend_x + 10, y + 8], fill=color)
            draw.text((legend_x + 15, y + 4), label, fill=text_color, 
                     font=font_label, anchor="lm")
        
        return img
    
    # Create the three plots
    plot_orig = create_plot(hist_orig_smooth, 'Original', is_difference=False)
    plot_edit = create_plot(hist_edited_smooth, 'Edited', is_difference=False)
    plot_diff = create_plot(hist_diff, 'Difference (E - O)', is_difference=True)
    
    return plot_orig, plot_edit, plot_diff
