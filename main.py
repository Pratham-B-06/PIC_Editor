import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import os

# Import our modules
from image_ops import ImageEditor
from utils import pil_to_tk
from analysis import edges, noise, histogram, sharpness, report, metrics, artifacts
from transform_tools import create_transform_tools

# --- Color Palette ---
BG_COLOR = "#1a1a1a"
PANEL_COLOR = "#2a2a2a"
BUTTON_COLOR = "#353535"
ACCENT_COLOR = "#ff9b00"
TEXT_COLOR = "#e6e6e6"
MUTED_TEXT_COLOR = "#bdbdbd"
PREVIEW_BG = "#121212"

class PyPicEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PyPic Editor Plus")
        self.root.geometry("1600x900")
        self.root.configure(bg=BG_COLOR)
        
        # State
        self.original_image = None
        self.current_image = None
        self.preview_image_tk = None
        self.analysis_results = {}

        # Slider storage
        self.sliders = {}
        self.slider_labels = {}

        # Default edit state template
        self.default_edit_state = {
            'rotate': 0,
            'gray': False,
            'sepia': False,
            'blur': False,
            'sharpen': False,
            'emboss': False,
            'vignette': False,
            'brightness': 1.0,
            'contrast': 1.0,
            'exposure': 1.0,
            'skew_x': 0,
            'skew_y': 0,
            'crop_box': None
        }
        self.edit_state = self.default_edit_state.copy()
        
        self.crop_mode = False
        self.crop_start = None
        self.crop_rect_id = None
        
        self.setup_theme()
        self.setup_layout()
        
    def setup_theme(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure Colors
        style.configure(".", background=BG_COLOR, foreground=TEXT_COLOR, borderwidth=0)
        style.configure("TFrame", background=BG_COLOR)
        style.configure("Panel.TFrame", background=PANEL_COLOR)
        
        # Label
        style.configure("TLabel", background=PANEL_COLOR, foreground=TEXT_COLOR, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground=ACCENT_COLOR)
        style.configure("Muted.TLabel", foreground=MUTED_TEXT_COLOR)
        
        # Button
        style.configure("TButton", 
                        background=BUTTON_COLOR, 
                        foreground=TEXT_COLOR, 
                        borderwidth=0, 
                        focuscolor=BG_COLOR,
                        font=("Segoe UI", 10))
        style.map("TButton", 
                  background=[('active', ACCENT_COLOR), ('pressed', ACCENT_COLOR)],
                  foreground=[('active', '#000000')])
        
        # Labelframe
        style.configure("TLabelframe", background=PANEL_COLOR, foreground=TEXT_COLOR, bordercolor=BUTTON_COLOR)
        style.configure("TLabelframe.Label", background=PANEL_COLOR, foreground=ACCENT_COLOR)
        
        # Notebook
        style.configure("TNotebook", background=PANEL_COLOR, borderwidth=0)
        style.configure("TNotebook.Tab", 
                        background=BUTTON_COLOR, 
                        foreground=TEXT_COLOR, 
                        padding=[10, 5], 
                        borderwidth=0)
        style.map("TNotebook.Tab", 
                  background=[('selected', PANEL_COLOR)],
                  foreground=[('selected', ACCENT_COLOR)])
        
        # Scale
        style.configure("Horizontal.TScale", background=PANEL_COLOR, troughcolor=BUTTON_COLOR, sliderlength=15)

        # Toolbutton (Toggle buttons)
        style.configure("Toolbutton", 
                        background=BUTTON_COLOR, 
                        foreground=TEXT_COLOR, 
                        borderwidth=0, 
                        focuscolor=BG_COLOR,
                        font=("Segoe UI", 10))
        style.map("Toolbutton", 
                  background=[('selected', ACCENT_COLOR), ('active', ACCENT_COLOR)],
                  foreground=[('selected', '#000000'), ('active', '#000000')])

    def setup_layout(self):
        # Main Container (3 Panels)
        # We use pack with side=left/right for fixed panels and fill=both for center
        
        # 1. Left Panel (Editing Tools) - Fixed Width
        self.left_panel = ttk.Frame(self.root, width=260, style="Panel.TFrame")
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        self.left_panel.pack_propagate(False) # Enforce width
        
        self.setup_left_panel()
        
        # 3. Right Panel (Analysis) - Fixed Width
        self.right_panel = ttk.Frame(self.root, width=380, style="Panel.TFrame")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=2, pady=2)
        self.right_panel.pack_propagate(False) # Enforce width
        
        self.setup_right_panel()
        
        # 2. Center Panel (Preview) - Expandable
        self.center_panel = ttk.Frame(self.root, style="Panel.TFrame")
        self.center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.setup_center_panel()

    def setup_left_panel(self):
        # Header
        ttk.Label(self.left_panel, text="Editing Tools", style="Header.TLabel").pack(pady=10, padx=10, anchor="w")
        
        # Tone Controls
        tone_frame = ttk.LabelFrame(self.left_panel, text="Tone Controls", padding=10)
        tone_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.create_slider(tone_frame, "Brightness", "brightness", -100, 100)
        self.create_slider(tone_frame, "Contrast", "contrast", -100, 100)
        self.create_slider(tone_frame, "Exposure", "exposure", -100, 100)
        self.create_slider(tone_frame, "Highlights", "highlights", -100, 100)
        
        # Filters & Effects
        filter_frame = ttk.LabelFrame(self.left_panel, text="Filters & Effects", padding=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Grid for filter buttons
        self.filter_vars = {}
        self.create_toggle_btn(filter_frame, "Grayscale", 'gray', 0, 0)
        self.create_toggle_btn(filter_frame, "Sepia", 'sepia', 0, 1)
        self.create_toggle_btn(filter_frame, "Blur", 'blur', 1, 0)
        self.create_toggle_btn(filter_frame, "Sharpen", 'sharpen', 1, 1)
        self.create_toggle_btn(filter_frame, "Vignette", 'vignette', 2, 0)
        self.create_toggle_btn(filter_frame, "Emboss", 'emboss', 2, 1)
        
        # NEW Transform Tools Section
        self.transform_section = create_transform_tools(self.left_panel, self)
        self.transform_section.pack(fill=tk.X, pady=10)
        
        # Action Buttons
        action_frame = ttk.Frame(self.left_panel, style="Panel.TFrame")
        action_frame.pack(fill=tk.X, padx=10, pady=20, side=tk.BOTTOM)
        
        ttk.Button(action_frame, text="Open Image", command=self.open_image).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Save Image", command=self.save_image).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Reset Image", command=self.reset_image).pack(fill=tk.X, pady=2)

    def create_toggle_btn(self, parent, text, key, row, col):
        var = tk.BooleanVar(value=False)
        self.filter_vars[key] = var
        # Use Toolbutton style for toggle look
        btn = ttk.Checkbutton(parent, text=text, variable=var, style="Toolbutton", command=lambda: self.on_filter_toggle(key))
        btn.grid(row=row, column=col, sticky="ew", padx=2, pady=2)
        try:
            parent.columnconfigure(col, weight=1)
        except Exception:
            pass

    def on_filter_toggle(self, key):
        # Update edit state from var
        self.edit_state[key] = self.filter_vars[key].get()
        print(f"DEBUG: Toggled {key} to {self.edit_state[key]}")
        self.apply_pipeline()

    def create_slider(self, parent, label, state_key, min_val, max_val):
        frame = ttk.Frame(parent, style="Panel.TFrame")
        frame.pack(fill=tk.X, pady=2)
        
        # Header with label and value
        header_frame = ttk.Frame(frame, style="Panel.TFrame")
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text=label).pack(side=tk.LEFT)
        
        # Value label
        value_label = ttk.Label(header_frame, text="0", style="Muted.TLabel")
        value_label.pack(side=tk.RIGHT)
        
        scale = ttk.Scale(frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL, command=lambda v: self.on_slider_change(state_key, v, value_label))
        scale.set(0)  # Explicitly set to 0
        scale.pack(fill=tk.X)
        
        # Initialize the label with the correct value
        if state_key in ['brightness', 'contrast', 'exposure', 'highlights']:
            value_label.config(text="0")
        
        # Store scale ref and label to reset later if needed
        self.sliders[state_key] = scale
        self.slider_labels[state_key] = value_label

    def setup_center_panel(self):
        # Header
        header = ttk.Frame(self.center_panel, style="Panel.TFrame")
        header.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header, text="Image Preview", style="Header.TLabel").pack(side=tk.LEFT)
        self.lbl_zoom = ttk.Label(header, text="100%", style="Muted.TLabel")
        self.lbl_zoom.pack(side=tk.RIGHT)
        
        # Canvas
        self.canvas_frame = ttk.Frame(self.center_panel)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg=PREVIEW_BG, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder text
        self.canvas_text = self.canvas.create_text(400, 300, text="No image loaded", fill=MUTED_TEXT_COLOR, font=("Segoe UI", 14))
        
        # Bind resize
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        
        # Bind mouse events for crop
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

    def setup_right_panel(self):
        # Header
        ttk.Label(self.right_panel, text="Analysis", style="Header.TLabel").pack(pady=10, padx=10, anchor="w")
        
        # Run Analysis Button
        ttk.Button(self.right_panel, text="RUN FULL ANALYSIS", command=self.run_analysis_thread).pack(fill=tk.X, padx=10, pady=5)
        
        # Notebook
        self.notebook = ttk.Notebook(self.right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tabs
        self.tab_edges = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.notebook.add(self.tab_edges, text="Edge")
        self.setup_edge_tab()
        
        self.tab_noise = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.notebook.add(self.tab_noise, text="Noise")
        self.setup_noise_tab()
        
        self.tab_hist = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.notebook.add(self.tab_hist, text="Hist")
        self.setup_hist_tab()
        
        self.tab_metrics = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.notebook.add(self.tab_metrics, text="Metrics")
        self.setup_metrics_tab()
        

        self.tab_art = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.notebook.add(self.tab_art, text="Artifacts")
        self.setup_artifacts_tab()
        
        self.tab_summary = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.notebook.add(self.tab_summary, text="Summary")
        self.setup_summary_tab()

    def setup_metrics_tab(self):
        container = ttk.Frame(self.tab_metrics, style="Panel.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.txt_metrics = tk.Text(container, height=15, bg=BUTTON_COLOR, fg=TEXT_COLOR, relief=tk.FLAT)
        self.txt_metrics.pack(fill=tk.BOTH, expand=True)
        self.txt_metrics.insert(tk.END, "Run analysis to see metrics.")


    def setup_artifacts_tab(self):
        container = ttk.Frame(self.tab_art, style="Panel.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.txt_art = tk.Text(container, height=10, bg=BUTTON_COLOR, fg=TEXT_COLOR, relief=tk.FLAT)
        self.txt_art.pack(fill=tk.BOTH, expand=True)
        self.txt_art.insert(tk.END, "Run analysis to see artifacts.")

    def setup_edge_tab(self):
        container = ttk.Frame(self.tab_edges, style="Panel.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Columns
        cols = ttk.Frame(container, style="Panel.TFrame")
        cols.pack(fill=tk.X)
        
        # Orig
        f1 = ttk.Frame(cols, style="Panel.TFrame")
        f1.pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Label(f1, text="Original Edges").pack()
        self.img_edge_orig = ttk.Label(f1, background="black") # Placeholder bg
        self.img_edge_orig.pack(pady=5)
        
        # Edited
        f2 = ttk.Frame(cols, style="Panel.TFrame")
        f2.pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Label(f2, text="Edited Edges").pack()
        self.img_edge_edit = ttk.Label(f2, background="black")
        self.img_edge_edit.pack(pady=5)
        
        # Diff
        ttk.Label(container, text="Difference (Green=New, Red=Lost)").pack(pady=(10,0))
        self.img_edge_diff = ttk.Label(container, background="black")
        self.img_edge_diff.pack(pady=5)
        
        self.lbl_edge_stats = ttk.Label(container, text="Stats: N/A", style="Muted.TLabel")
        self.lbl_edge_stats.pack(pady=10)

    def setup_noise_tab(self):
        container = ttk.Frame(self.tab_noise, style="Panel.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(container, text="Noise Analysis").pack()
        self.txt_noise = tk.Text(container, height=10, bg=BUTTON_COLOR, fg=TEXT_COLOR, relief=tk.FLAT)
        self.txt_noise.pack(fill=tk.BOTH, expand=True, pady=5)
        self.txt_noise.insert(tk.END, "Run analysis to see results.")

    def setup_hist_tab(self):
        container = ttk.Frame(self.tab_hist, style="Panel.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(container, text="Histogram Analysis").pack()
        self.txt_hist = tk.Text(container, height=5, bg=BUTTON_COLOR, fg=TEXT_COLOR, relief=tk.FLAT)
        self.txt_hist.pack(fill=tk.X, pady=5)
        self.txt_hist.insert(tk.END, "Run analysis to see results.")
        
        # Histogram Plots - VERTICAL LAYOUT
        plots_frame = ttk.Frame(container, style="Panel.TFrame")
        plots_frame.pack(fill=tk.BOTH, expand=True)
        
        # Original
        ttk.Label(plots_frame, text="Original Image").pack(pady=(5,0))
        self.lbl_hist_orig = ttk.Label(plots_frame, background="#2a2a2a")
        self.lbl_hist_orig.pack(fill=tk.X, pady=2)
        
        # Edited
        ttk.Label(plots_frame, text="Edited Image").pack(pady=(5,0))
        self.lbl_hist_edit = ttk.Label(plots_frame, background="#2a2a2a")
        self.lbl_hist_edit.pack(fill=tk.X, pady=2)
        
        # Difference
        ttk.Label(plots_frame, text="Difference (Edited - Original)").pack(pady=(5,0))
        self.lbl_hist_diff = ttk.Label(plots_frame, background="#2a2a2a")
        self.lbl_hist_diff.pack(fill=tk.X, pady=2)
        
        # Export button
        ttk.Button(container, text="Export Histograms", command=self.save_histograms).pack(fill=tk.X, pady=(5,0))
        self.lbl_hist_diff.pack(pady=5)

    def setup_summary_tab(self):
        container = ttk.Frame(self.tab_summary, style="Panel.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.txt_summary = tk.Text(container, height=15, bg=BUTTON_COLOR, fg=TEXT_COLOR, relief=tk.FLAT)
        self.txt_summary.pack(fill=tk.BOTH, expand=True, pady=5)
        
        btn_frame = ttk.Frame(container, style="Panel.TFrame")
        btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Export Report", command=self.export_report).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(btn_frame, text="Save Histograms", command=self.save_histograms).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

    # --- Logic ---

    def open_image(self):
        print("DEBUG: Open Image clicked")
        try:
            path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tiff")])
            print(f"DEBUG: File dialog returned: {path}")
            if path:
                self.original_image = Image.open(path).convert("RGB")
                self.current_image = self.original_image.copy()
                print("DEBUG: Image loaded successfully")
                self.update_preview()
                self.reset_controls()
        except Exception as e:
            print(f"ERROR in open_image: {e}")
            messagebox.showerror("Error", f"Failed to open image: {e}")

    def save_image(self):
        print("DEBUG: Save Image clicked")
        if not self.current_image:
            print("DEBUG: No current image to save")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
        if path:
            self.current_image.save(path)
            messagebox.showinfo("Saved", "Image saved successfully.")

    def reset_image(self):
        print("DEBUG: Reset Image clicked")
        if self.original_image:
            self.current_image = self.original_image.copy()
            self.update_preview()
            self.reset_controls()
        else:
            print("DEBUG: No original image to reset")

    def reset_controls(self):
        # Reset sliders to neutral (0)
        for key, scale in self.sliders.items():
            try:
                scale.set(0)
            except Exception:
                pass
        
        # Also reset the value labels
        for key, label in self.slider_labels.items():
            try:
                label.config(text="0")
            except Exception:
                pass
        
        # Reset toggle buttons
        if hasattr(self, 'filter_vars'):
            for key, var in self.filter_vars.items():
                var.set(False)
        

        # Restore default edit state
        self.edit_state = self.default_edit_state.copy()

    def on_slider_change(self, key, value, label=None):
        # print(f"DEBUG: Slider {key} changed to {value}") # Commented out to avoid spam
        val = float(value)
        
        if key in ['brightness', 'contrast', 'exposure', 'highlights']:
            # Map -100..100 to multiplier
            # 0 -> 1.0
            # 100 -> 2.0
            # -100 -> 0.5
            # Formula: 2^(val/100)
            multiplier = 2 ** (val / 100.0)
            self.edit_state[key] = multiplier
            if label:
                label.config(text=f"{int(val):+d}")
        else:
            # numeric sliders other than tone map directly; ensure numeric zero default
            try:
                numeric_val = float(val)
            except Exception:
                numeric_val = val
            self.edit_state[key] = numeric_val
            if label:
                label.config(text=f"{int(val)}")
            
        self.apply_pipeline()

    def apply_transform(self, type_):
        print(f"DEBUG: apply_transform called with {type_}")
        if not self.original_image:
            print("DEBUG: No original image, ignoring transform")
            return
        
        if type_ == 'rotate_left':
            self.edit_state['rotate'] += 90
        elif type_ == 'rotate_right':
            self.edit_state['rotate'] -= 90
        elif type_ == 'crop':
            self.toggle_crop_mode()
            return

        elif type_ in ['gray', 'sepia', 'blur', 'sharpen', 'emboss', 'vignette']:
            # This path is now only for programmatic calls if any, as buttons use on_filter_toggle
            pass
            
        self.apply_pipeline()

    def toggle_crop_mode(self):
        self.crop_mode = not self.crop_mode
        if self.crop_mode:
            self.canvas.config(cursor="crosshair")
            messagebox.showinfo("Crop Mode", "Drag on the image to crop. Release to apply.")
        else:
            self.canvas.config(cursor="")
            if self.crop_rect_id:
                self.canvas.delete(self.crop_rect_id)
                self.crop_rect_id = None

    def on_canvas_click(self, event):
        if not self.crop_mode or not self.current_image: return
        self.crop_start = (event.x, event.y)
        if self.crop_rect_id:
            self.canvas.delete(self.crop_rect_id)
        self.crop_rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="white", width=2, dash=(4, 4))

    def on_canvas_drag(self, event):
        if not self.crop_mode or not self.crop_start: return
        x0, y0 = self.crop_start
        self.canvas.coords(self.crop_rect_id, x0, y0, event.x, event.y)

    def on_canvas_release(self, event):
        if not self.crop_mode or not self.crop_start: return
        x0, y0 = self.crop_start
        x1, y1 = event.x, event.y
        
        # Normalize coords
        x_start, x_end = sorted([x0, x1])
        y_start, y_end = sorted([y0, y1])
        
        # Convert canvas coords to image coords
        w_canvas = self.canvas.winfo_width()
        h_canvas = self.canvas.winfo_height()
        
        img_w, img_h = self.current_image.size
        
        # Calculate scale used in update_preview
        scale_w = w_canvas / img_w if img_w > 0 else 1
        scale_h = h_canvas / img_h if img_h > 0 else 1
        scale = min(scale_w, scale_h)
        
        disp_w = int(img_w * scale)
        disp_h = int(img_h * scale)
        
        off_x = (w_canvas - disp_w) // 2
        off_y = (h_canvas - disp_h) // 2
        
        crop_x0 = int((x_start - off_x) / scale)
        crop_y0 = int((y_start - off_y) / scale)
        crop_x1 = int((x_end - off_x) / scale)
        crop_y1 = int((y_end - off_y) / scale)
        
        # Clamp
        crop_x0 = max(0, crop_x0)
        crop_y0 = max(0, crop_y0)
        crop_x1 = min(img_w, crop_x1)
        crop_y1 = min(img_h, crop_y1)
        
        if crop_x1 - crop_x0 > 10 and crop_y1 - crop_y0 > 10:
            cropped_img = self.current_image.crop((crop_x0, crop_y0, crop_x1, crop_y1))
            self.original_image = cropped_img
            self.current_image = cropped_img.copy()
            self.reset_controls() # Reset controls since crop bakes current view
            self.update_preview()
            self.toggle_crop_mode() # Exit crop mode
        else:
            messagebox.showwarning("Invalid Crop", "Crop area too small.")

    def apply_pipeline(self):
        if not self.original_image:
            print("DEBUG: apply_pipeline called but no original image")
            return
        
        try:
            print("DEBUG: Applying pipeline...")
            img = self.original_image.copy()
            
            # 1. Rotation & Skew
            if self.edit_state.get('rotate', 0) != 0:
                img = ImageEditor.rotate(img, self.edit_state.get('rotate', 0))
                
            if self.edit_state.get('skew_x', 0) != 0:
                img = ImageEditor.skew(img, self.edit_state.get('skew_x', 0), 'horizontal')
                
            if self.edit_state.get('skew_y', 0) != 0:
                img = ImageEditor.skew(img, self.edit_state.get('skew_y', 0), 'vertical')
                

            # 2. Filters
            if self.edit_state.get('gray'): img = ImageEditor.to_grayscale(img)
            if self.edit_state.get('sepia'): img = ImageEditor.apply_sepia(img)
            if self.edit_state.get('blur'): img = ImageEditor.blur(img)
            if self.edit_state.get('sharpen'): img = ImageEditor.sharpen(img)
            if self.edit_state.get('emboss'): img = ImageEditor.apply_emboss(img)
            if self.edit_state.get('vignette'): img = ImageEditor.apply_vignette(img)
                
            # 3. Tone
            if self.edit_state.get('brightness', 1.0) != 1.0:
                img = ImageEditor.adjust_brightness(img, self.edit_state.get('brightness', 1.0))
            if self.edit_state.get('contrast', 1.0) != 1.0:
                img = ImageEditor.adjust_contrast(img, self.edit_state.get('contrast', 1.0))
            if self.edit_state.get('exposure', 1.0) != 1.0:
                img = ImageEditor.adjust_exposure(img, self.edit_state.get('exposure', 1.0))
            if self.edit_state.get('highlights', 1.0) != 1.0:
                img = ImageEditor.adjust_highlights(img, self.edit_state.get('highlights', 1.0))
                
            self.current_image = img
            print(f"DEBUG: Pipeline applied successfully, current_image is now {type(self.current_image)} size {self.current_image.size if self.current_image else 'None'}")
            self.update_preview()
        except Exception as e:
            print(f"ERROR in pipeline: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to apply effects: {e}")
            # Don't clear current_image on error - keep the last good state
            if not hasattr(self, 'current_image') or self.current_image is None:
                print("ERROR: current_image is None after error, restoring from original")
                self.current_image = self.original_image.copy()
                self.update_preview()

    def update_preview(self):
        if not self.current_image:
            # show placeholder text
            self.canvas.delete("all")
            self.canvas.create_text(400, 300, text="No image loaded", fill=MUTED_TEXT_COLOR, font=("Segoe UI", 14))
            return
        
        # Get canvas size
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10: w = 800
        if h < 10: h = 600
        
        # Resize maintaining aspect ratio
        img_copy = self.current_image.copy()
        img_copy.thumbnail((w, h), Image.Resampling.LANCZOS)
        
        self.preview_image_tk = ImageTk.PhotoImage(img_copy)
        self.canvas.delete("all")
        self.canvas.create_image(w//2, h//2, image=self.preview_image_tk, anchor=tk.CENTER)
        
        # Update zoom label (approx)
        zoom = min(w/self.current_image.width, h/self.current_image.height) * 100
        try:
            self.lbl_zoom.config(text=f"{int(zoom)}%")
        except Exception:
            pass

    def on_canvas_resize(self, event):
        if self.current_image:
            self.update_preview()
        else:
            self.canvas.delete("all")
            self.canvas.create_text(event.width//2, event.height//2, text="No image loaded", fill=MUTED_TEXT_COLOR, font=("Segoe UI", 14))

    def run_analysis_thread(self):
        if not hasattr(self, 'original_image') or self.original_image is None:
            messagebox.showerror("Error", "Please load an image first using the 'Open Image' button.")
            return
        if not hasattr(self, 'current_image') or self.current_image is None:
            messagebox.showerror("Error", "Current image is missing. Please reload the image.")
            return
        
        print(f"DEBUG: Running analysis - Original: {self.original_image.size}, Current: {self.current_image.size}")
        t = threading.Thread(target=self.run_analysis, daemon=True)
        t.start()

    def run_analysis(self):
        try:
            # Resize for analysis
            ana_w, ana_h = 800, 800
            img_orig_small = self.original_image.copy()
            img_orig_small.thumbnail((ana_w, ana_h))
            
            img_edit_small = self.current_image.copy()
            img_edit_small.thumbnail((ana_w, ana_h))
            
            # Ensure both images are same size for analysis
            if img_orig_small.size != img_edit_small.size:
                img_edit_small = img_edit_small.resize(img_orig_small.size, Image.Resampling.LANCZOS)
            
            # Run modules
            edge_res = edges.analyze_edges(img_orig_small, img_edit_small)
            noise_res = noise.analyze_noise(img_orig_small, img_edit_small)
            hist_res = histogram.analyze_histogram(img_orig_small, img_edit_small)
            sharp_res = sharpness.analyze_sharpness(img_orig_small, img_edit_small)
            
            # New modules
            metric_res = metrics.analyze_metrics(img_orig_small, img_edit_small)

            art_comp = artifacts.detect_compression_artifacts(img_edit_small)
            art_smooth = artifacts.detect_oversmoothing(img_edit_small)
            
            self.root.after(0, lambda: self.update_analysis_ui(edge_res, noise_res, hist_res, sharp_res, metric_res, art_comp, art_smooth))
        except Exception as e:
            print(f"ERROR in run_analysis: {e}")
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: messagebox.showerror("Analysis Error", f"Analysis failed:\n{str(e)}"))

    def update_analysis_ui(self, edge_res, noise_res, hist_res, sharp_res, metric_res, art_comp, art_smooth):
        # Edge Tab Images
        self.tk_edge_orig = pil_to_tk(edge_res['orig_edge'], (150, 150))
        self.img_edge_orig.config(image=self.tk_edge_orig)
        
        self.tk_edge_edit = pil_to_tk(edge_res['edited_edge'], (150, 150))
        self.img_edge_edit.config(image=self.tk_edge_edit)
        
        self.tk_edge_diff = pil_to_tk(edge_res['difference_map'], (300, 200))
        self.img_edge_diff.config(image=self.tk_edge_diff)
        
        self.lbl_edge_stats.config(text=f"Density Delta: {edge_res['density_delta']:.3f}")
        
        # Noise Tab Text
        self.txt_noise.delete("1.0", tk.END)
        self.txt_noise.insert(tk.END, f"Original Noise: {noise_res['noise_original']:.3f}\n")
        self.txt_noise.insert(tk.END, f"Edited Noise: {noise_res['noise_edited']:.3f}\n")
        self.txt_noise.insert(tk.END, f"Delta: {noise_res['noise_delta']:.3f}\n")
        
        # Hist Tab Text
        self.txt_hist.delete("1.0", tk.END)
        self.txt_hist.insert(tk.END, f"Brightness Delta: {hist_res['brightness_delta']:.2f}\n")
        self.txt_hist.insert(tk.END, f"Contrast Delta: {hist_res['contrast_delta']:.2f}\n")
        
        # Hist Plots
        self.tk_hist_orig = pil_to_tk(hist_res['plot_original'], (170, 100))
        self.lbl_hist_orig.config(image=self.tk_hist_orig)
        
        self.tk_hist_edit = pil_to_tk(hist_res['plot_edited'], (170, 100))
        self.lbl_hist_edit.config(image=self.tk_hist_edit)
        
        self.tk_hist_diff = pil_to_tk(hist_res['plot_diff'], (340, 100))
        self.lbl_hist_diff.config(image=self.tk_hist_diff)
        
        # Metrics Tab
        self.txt_metrics.delete("1.0", tk.END)
        self.txt_metrics.insert(tk.END, f"MSE: {metric_res['mse']:.2f}\n")
        self.txt_metrics.insert(tk.END, f"PSNR: {metric_res['psnr']:.2f} dB\n")
        self.txt_metrics.insert(tk.END, f"SSIM: {metric_res['ssim']:.4f}\n")
        self.txt_metrics.insert(tk.END, f"SNR (Orig): {metric_res['snr_orig']:.2f} dB\n")
        self.txt_metrics.insert(tk.END, f"SNR (Edit): {metric_res['snr_edit']:.2f} dB\n")
        self.txt_metrics.insert(tk.END, f"Entropy (Orig): {metric_res['entropy_orig']:.2f}\n")
        self.txt_metrics.insert(tk.END, f"Entropy (Edit): {metric_res['entropy_edit']:.2f}\n")
        
        
        # Artifacts Tab
        self.txt_art.delete("1.0", tk.END)
        self.txt_art.insert(tk.END, f"Compression Score: {art_comp:.2f}\n")
        self.txt_art.insert(tk.END, f"Oversmoothing Score: {art_smooth:.2f}\n")
        
        # Summary Tab
        summary = report.generate_summary_text(
            edge_res, noise_res, hist_res, sharp_res,
            metric_data=metric_res,
            art_data={'compression': art_comp, 'smoothing': art_smooth}
        )
        self.txt_summary.delete("1.0", tk.END)
        self.txt_summary.insert(tk.END, summary)
        
        # Store histogram plots for later export
        self.current_hist_plots = {
            'original': hist_res['plot_original'],
            'edited': hist_res['plot_edited'],
            'diff': hist_res['plot_diff'],
            'combined': hist_res['plot_combined']  # Combined vertical image
        }
        
        messagebox.showinfo("Analysis Complete", "Analysis finished.")

    def save_histograms(self):
        if not hasattr(self, 'current_hist_plots'):
            messagebox.showerror("Error", "Run analysis first!")
            return
        
        # Check if we have combined plot
        if 'combined' not in self.current_hist_plots:
            messagebox.showerror("Error", "Combined histogram not available. Please run analysis again.")
            return
            
        path = filedialog.asksaveasfilename(
            defaultextension=".png", 
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")],
            title="Save Combined Histograms"
        )
        if path:
            try:
                self.current_hist_plots['combined'].save(path)
                messagebox.showinfo("Saved", f"Combined histograms saved to:\n{path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save histograms: {e}")

    def export_report(self):
        text = self.txt_summary.get("1.0", tk.END)
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text File", "*.txt")])
        if path:
            report.save_report_txt(text, path)
            messagebox.showinfo("Exported", f"Report saved to {path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PyPicEditorApp(root)
    root.mainloop()
