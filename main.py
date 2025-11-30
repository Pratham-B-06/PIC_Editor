import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import os

from image_ops import ImageEditor
from utils import pil_to_tk
from analysis import edges, noise, histogram, sharpness, report, metrics, artifacts
from transform_tools import create_transform_tools
from crop_box import CropBox

# --- Color Palette / Theme ---
BG_COLOR = "#1a1a1a"
PANEL_COLOR = "#2a2a2a"
BUTTON_COLOR = "#353535"
ACCENT_COLOR = "#ff9b00"
TEXT_COLOR = "#e6e6e6"
MUTED_TEXT_COLOR = "#bdbdbd"
PREVIEW_BG = "#121212"


class PyPicEditorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PyPic Editor Plus")
        self.root.geometry("1600x900")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(1100, 700)

        # Image state
        self.original_image = None
        self.current_image = None
        self.preview_image_tk = None

        # Analysis results
        self.analysis_results = {}

        # UI state
        self.sliders = {}
        self.slider_labels = {}
        self.filter_vars = {}
        self.transform_buttons = {}
        self.transform_section = None

        # Crop state
        self.crop_box = None
        self.crop_active = False
        self.crop_buttons_frame = None

        # Default edit state
        self.default_edit_state = {
            "rotate": 0,
            "gray": False,
            "sepia": False,
            "blur": False,
            "sharpen": False,
            "emboss": False,
            "vignette": False,
            "brightness": 1.0,
            "contrast": 1.0,
            "exposure": 1.0,
            "highlights": 1.0,
            "skew_x": 0,
            "skew_y": 0,
            "crop_box": None,
        }
        self.edit_state = self.default_edit_state.copy()

        # Canvas default bindings
        self._default_canvas_bindings = {
            "<Button-1>": None,
            "<B1-Motion>": None,
            "<ButtonRelease-1>": None,
        }

        self.setup_theme()
        self.setup_layout()

    # ================= THEME =================

    def setup_theme(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=BG_COLOR, foreground=TEXT_COLOR, borderwidth=0)
        style.configure("TFrame", background=BG_COLOR)
        style.configure("Panel.TFrame", background=PANEL_COLOR)

        style.configure(
            "TLabel",
            background=PANEL_COLOR,
            foreground=TEXT_COLOR,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Header.TLabel",
            font=("Segoe UI", 12, "bold"),
            foreground=ACCENT_COLOR,
        )
        style.configure("Muted.TLabel", foreground=MUTED_TEXT_COLOR)

        style.configure(
            "TButton",
            background=BUTTON_COLOR,
            foreground=TEXT_COLOR,
            borderwidth=0,
            focuscolor=BG_COLOR,
            font=("Segoe UI", 10),
        )
        style.map(
            "TButton",
            background=[("active", ACCENT_COLOR), ("pressed", ACCENT_COLOR)],
            foreground=[("active", "#000000")],
        )

        style.configure(
            "TLabelframe",
            background=PANEL_COLOR,
            foreground=TEXT_COLOR,
            bordercolor=BUTTON_COLOR,
        )
        style.configure(
            "TLabelframe.Label",
            background=PANEL_COLOR,
            foreground=ACCENT_COLOR,
        )

        style.configure("TNotebook", background=PANEL_COLOR, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=BUTTON_COLOR,
            foreground=TEXT_COLOR,
            padding=[10, 5],
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", PANEL_COLOR)],
            foreground=[("selected", ACCENT_COLOR)],
        )

        style.configure(
            "Horizontal.TScale",
            background=PANEL_COLOR,
            troughcolor=BUTTON_COLOR,
            sliderlength=15,
        )

        style.configure(
            "Toolbutton",
            background=BUTTON_COLOR,
            foreground=TEXT_COLOR,
            borderwidth=0,
            focuscolor=BG_COLOR,
            font=("Segoe UI", 10),
        )
        style.map(
            "Toolbutton",
            background=[("selected", ACCENT_COLOR), ("active", ACCENT_COLOR)],
            foreground=[("selected", "#000000"), ("active", "#000000")],
        )

    # ================= LAYOUT =================

    def setup_layout(self):
        # Left panel (tools)
        self.left_panel = ttk.Frame(self.root, width=260, style="Panel.TFrame")
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        self.left_panel.pack_propagate(False)
        self.setup_left_panel()

        # Right panel (analysis)
        self.right_panel = ttk.Frame(self.root, width=380, style="Panel.TFrame")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=2, pady=2)
        self.right_panel.pack_propagate(False)
        self.setup_right_panel()

        # Center (preview)
        self.center_panel = ttk.Frame(self.root, style="Panel.TFrame")
        self.center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.setup_center_panel()

    # ----- Left panel -----

    def setup_left_panel(self):
        ttk.Label(
            self.left_panel, text="Editing Tools", style="Header.TLabel"
        ).pack(pady=10, padx=10, anchor="w")

        # Tone controls
        tone_frame = ttk.LabelFrame(self.left_panel, text="Tone Controls", padding=10)
        tone_frame.pack(fill=tk.X, padx=10, pady=5)
        self.create_slider(tone_frame, "Brightness", "brightness", -100, 100)
        self.create_slider(tone_frame, "Contrast", "contrast", -100, 100)
        self.create_slider(tone_frame, "Exposure", "exposure", -100, 100)
        self.create_slider(tone_frame, "Highlights", "highlights", -100, 100)

        # Filters
        filter_frame = ttk.LabelFrame(self.left_panel, text="Filters & Effects", padding=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        self.create_toggle_btn(filter_frame, "Grayscale", "gray", 0, 0)
        self.create_toggle_btn(filter_frame, "Sepia", "sepia", 0, 1)
        self.create_toggle_btn(filter_frame, "Blur", "blur", 1, 0)
        self.create_toggle_btn(filter_frame, "Sharpen", "sharpen", 1, 1)
        self.create_toggle_btn(filter_frame, "Vignette", "vignette", 2, 0)
        self.create_toggle_btn(filter_frame, "Emboss", "emboss", 2, 1)

        # Transform tools (rotate, crop, skew)
        self.transform_section = create_transform_tools(self.left_panel, self)
        self.transform_section.pack(fill=tk.X, pady=10)

        # Bottom actions
        action_frame = ttk.Frame(self.left_panel, style="Panel.TFrame")
        action_frame.pack(fill=tk.X, padx=10, pady=20, side=tk.BOTTOM)
        ttk.Button(action_frame, text="Open Image", command=self.open_image).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(action_frame, text="Save Image", command=self.save_image).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(action_frame, text="Reset Image", command=self.reset_image).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(action_frame, text="Crop", command=self.toggle_crop_mode).pack(
            fill=tk.X, pady=2
        )

    def create_toggle_btn(self, parent, text, key, row, col):
        var = tk.BooleanVar(value=False)
        self.filter_vars[key] = var
        btn = ttk.Checkbutton(
            parent,
            text=text,
            variable=var,
            style="Toolbutton",
            command=lambda: self.on_filter_toggle(key),
        )
        btn.grid(row=row, column=col, sticky="ew", padx=2, pady=2)
        try:
            parent.columnconfigure(col, weight=1)
        except Exception:
            pass

    def on_filter_toggle(self, key):
        self.edit_state[key] = self.filter_vars[key].get()
        self.apply_pipeline()

    def create_slider(self, parent, label, state_key, min_val, max_val):
        frame = ttk.Frame(parent, style="Panel.TFrame")
        frame.pack(fill=tk.X, pady=2)

        header_frame = ttk.Frame(frame, style="Panel.TFrame")
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text=label).pack(side=tk.LEFT)

        value_label = ttk.Label(header_frame, text="0", style="Muted.TLabel")
        value_label.pack(side=tk.RIGHT)

        scale = ttk.Scale(
            frame,
            from_=min_val,
            to=max_val,
            orient=tk.HORIZONTAL,
            command=lambda v: self.on_slider_change(state_key, v, value_label),
        )
        scale.set(0)
        scale.pack(fill=tk.X)

        self.sliders[state_key] = scale
        self.slider_labels[state_key] = value_label

    # ----- Center panel -----

    def setup_center_panel(self):
        header = ttk.Frame(self.center_panel, style="Panel.TFrame")
        header.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(header, text="Image Preview", style="Header.TLabel").pack(side=tk.LEFT)
        self.lbl_zoom = ttk.Label(header, text="100%", style="Muted.TLabel")
        self.lbl_zoom.pack(side=tk.RIGHT)

        self.canvas_frame = ttk.Frame(self.center_panel, style="Panel.TFrame")
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.canvas_frame, bg=PREVIEW_BG, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas_text = self.canvas.create_text(
            400,
            300,
            text="No image loaded",
            fill=MUTED_TEXT_COLOR,
            font=("Segoe UI", 14),
        )

        self.canvas.bind("<Configure>", self.on_canvas_resize)

        # Default handlers (no-op but kept for future tools)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        self._default_canvas_bindings["<Button-1>"] = self.on_canvas_click
        self._default_canvas_bindings["<B1-Motion>"] = self.on_canvas_drag
        self._default_canvas_bindings["<ButtonRelease-1>"] = self.on_canvas_release

    def on_canvas_click(self, event):
        # Reserved for future tools (pan, pick, etc.)
        pass

    def on_canvas_drag(self, event):
        pass

    def on_canvas_release(self, event):
        pass

    # ----- Right panel -----

    def setup_right_panel(self):
        ttk.Label(
            self.right_panel, text="Analysis", style="Header.TLabel"
        ).pack(pady=10, padx=10, anchor="w")

        ttk.Button(
            self.right_panel, text="RUN FULL ANALYSIS", command=self.run_analysis_thread
        ).pack(fill=tk.X, padx=10, pady=5)

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
        self.txt_metrics = tk.Text(
            container, height=15, bg=BUTTON_COLOR, fg=TEXT_COLOR, relief=tk.FLAT
        )
        self.txt_metrics.pack(fill=tk.BOTH, expand=True)
        self.txt_metrics.insert(tk.END, "Run analysis to see metrics.")

    def setup_artifacts_tab(self):
        container = ttk.Frame(self.tab_art, style="Panel.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.txt_art = tk.Text(
            container, height=10, bg=BUTTON_COLOR, fg=TEXT_COLOR, relief=tk.FLAT
        )
        self.txt_art.pack(fill=tk.BOTH, expand=True)
        self.txt_art.insert(tk.END, "Run analysis to see artifacts.")

    # ===== Edge tab: vertical layout, unified size =====

    def setup_edge_tab(self):
        container = ttk.Frame(self.tab_edges, style="Panel.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.edge_target_size = (300, 200)

        ttk.Label(container, text="Original Edges").pack(pady=(0, 3))
        self.img_edge_orig = ttk.Label(container, background="black")
        self.img_edge_orig.pack(pady=5)

        ttk.Label(container, text="Edited Edges").pack(pady=(10, 3))
        self.img_edge_edit = ttk.Label(container, background="black")
        self.img_edge_edit.pack(pady=5)

        ttk.Label(container, text="Difference (Green=New, Red=Lost)").pack(pady=(10, 3))
        self.img_edge_diff = ttk.Label(container, background="black")
        self.img_edge_diff.pack(pady=5)

        self.lbl_edge_stats = ttk.Label(
            container, text="Stats: N/A", style="Muted.TLabel"
        )
        self.lbl_edge_stats.pack(pady=10)

    def setup_noise_tab(self):
        container = ttk.Frame(self.tab_noise, style="Panel.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(container, text="Noise Analysis").pack()
        self.txt_noise = tk.Text(
            container, height=10, bg=BUTTON_COLOR, fg=TEXT_COLOR, relief=tk.FLAT
        )
        self.txt_noise.pack(fill=tk.BOTH, expand=True, pady=5)
        self.txt_noise.insert(tk.END, "Run analysis to see results.")

    def setup_hist_tab(self):
        container = ttk.Frame(self.tab_hist, style="Panel.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(container, text="Histogram Analysis").pack()
        self.txt_hist = tk.Text(
            container, height=5, bg=BUTTON_COLOR, fg=TEXT_COLOR, relief=tk.FLAT
        )
        self.txt_hist.pack(fill=tk.X, pady=5)
        self.txt_hist.insert(tk.END, "Run analysis to see results.")

        plots_frame = ttk.Frame(container, style="Panel.TFrame")
        plots_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(plots_frame, text="Original Image").pack(pady=(5, 0))
        self.lbl_hist_orig = ttk.Label(plots_frame, background="#2a2a2a")
        self.lbl_hist_orig.pack(fill=tk.X, pady=2)

        ttk.Label(plots_frame, text="Edited Image").pack(pady=(5, 0))
        self.lbl_hist_edit = ttk.Label(plots_frame, background="#2a2a2a")
        self.lbl_hist_edit.pack(fill=tk.X, pady=2)

        ttk.Label(plots_frame, text="Difference (Edited - Original)").pack(pady=(5, 0))
        self.lbl_hist_diff = ttk.Label(plots_frame, background="#2a2a2a")
        self.lbl_hist_diff.pack(fill=tk.X, pady=2)

        ttk.Button(
            container, text="Export Histograms", command=self.save_histograms
        ).pack(fill=tk.X, pady=(5, 0))

    def setup_summary_tab(self):
        container = ttk.Frame(self.tab_summary, style="Panel.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.txt_summary = tk.Text(
            container, height=15, bg=BUTTON_COLOR, fg=TEXT_COLOR, relief=tk.FLAT
        )
        self.txt_summary.pack(fill=tk.BOTH, expand=True, pady=5)

        btn_frame = ttk.Frame(container, style="Panel.TFrame")
        btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Export Report", command=self.export_report).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=2
        )
        ttk.Button(
            btn_frame,
            text="Export Edge Detection",
            command=self.export_edge_detection,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

    # ================= CORE IMAGE LOGIC =================

    def open_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        if not path:
            return
        try:
            self.original_image = Image.open(path).convert("RGB")
            self.current_image = self.original_image.copy()
            self.update_preview()
            self.reset_controls()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image: {e}")

    def save_image(self):
        if not self.current_image:
            messagebox.showwarning("No Image", "There is no image to save.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")],
        )
        if not path:
            return
        try:
            self.current_image.save(path)
            messagebox.showinfo("Saved", "Image saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {e}")

    def reset_image(self):
        if not self.original_image:
            return
        self.current_image = self.original_image.copy()
        self.update_preview()
        self.reset_controls()

    def reset_controls(self):
        for scale in self.sliders.values():
            try:
                scale.set(0)
            except Exception:
                pass

        for label in self.slider_labels.values():
            try:
                label.config(text="0")
            except Exception:
                pass

        for var in self.filter_vars.values():
            var.set(False)

        self.edit_state = self.default_edit_state.copy()

    def on_slider_change(self, key, value, label=None):
        val = float(value)
        if key in ["brightness", "contrast", "exposure", "highlights"]:
            multiplier = 2 ** (val / 100.0)
            self.edit_state[key] = multiplier
            if label:
                label.config(text=f"{int(val):+d}")
        else:
            self.edit_state[key] = val
            if label:
                label.config(text=f"{int(val)}")
        self.apply_pipeline()

    def apply_transform(self, type_):
        if not self.original_image:
            return
        if type_ == "rotate_left":
            self.edit_state["rotate"] += 90
        elif type_ == "rotate_right":
            self.edit_state["rotate"] -= 90
        elif type_ == "crop":
            self.toggle_crop_mode()
            return
        self.apply_pipeline()

    def apply_pipeline(self):
        if not self.original_image:
            return
        try:
            img = self.original_image.copy()

            # Rotation & skew
            if self.edit_state.get("rotate", 0) != 0:
                img = ImageEditor.rotate(img, self.edit_state["rotate"])
            if self.edit_state.get("skew_x", 0) != 0:
                img = ImageEditor.skew(img, self.edit_state["skew_x"], "horizontal")
            if self.edit_state.get("skew_y", 0) != 0:
                img = ImageEditor.skew(img, self.edit_state["skew_y"], "vertical")

            # Filters
            if self.edit_state.get("gray"):
                img = ImageEditor.to_grayscale(img)
            if self.edit_state.get("sepia"):
                img = ImageEditor.apply_sepia(img)
            if self.edit_state.get("blur"):
                img = ImageEditor.blur(img)
            if self.edit_state.get("sharpen"):
                img = ImageEditor.sharpen(img)
            if self.edit_state.get("emboss"):
                img = ImageEditor.apply_emboss(img)
            if self.edit_state.get("vignette"):
                img = ImageEditor.apply_vignette(img)

            # Tone
            if self.edit_state.get("brightness", 1.0) != 1.0:
                img = ImageEditor.adjust_brightness(img, self.edit_state["brightness"])
            if self.edit_state.get("contrast", 1.0) != 1.0:
                img = ImageEditor.adjust_contrast(img, self.edit_state["contrast"])
            if self.edit_state.get("exposure", 1.0) != 1.0:
                img = ImageEditor.adjust_exposure(img, self.edit_state["exposure"])
            if self.edit_state.get("highlights", 1.0) != 1.0:
                img = ImageEditor.adjust_highlights(img, self.edit_state["highlights"])

            self.current_image = img
            self.update_preview()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply effects: {e}")
            if self.original_image is not None and self.current_image is None:
                self.current_image = self.original_image.copy()
                self.update_preview()

    def update_preview(self):
        if not self.current_image:
            self.canvas.delete("all")
            self.canvas.create_text(
                400,
                300,
                text="No image loaded",
                fill=MUTED_TEXT_COLOR,
                font=("Segoe UI", 14),
            )
            return

        w = self.canvas.winfo_width() or 800
        h = self.canvas.winfo_height() or 600

        img_copy = self.current_image.copy()
        img_copy.thumbnail((w, h), Image.Resampling.LANCZOS)

        self.preview_image_tk = ImageTk.PhotoImage(img_copy)
        self.canvas.delete("all")
        self.canvas.create_image(w // 2, h // 2, image=self.preview_image_tk, anchor=tk.CENTER)

        zoom = min(w / self.current_image.width, h / self.current_image.height) * 100
        self.lbl_zoom.config(text=f"{int(zoom)}%")

    def on_canvas_resize(self, event):
        if self.current_image:
            self.update_preview()
        else:
            self.canvas.delete("all")
            self.canvas.create_text(
                event.width // 2,
                event.height // 2,
                text="No image loaded",
                fill=MUTED_TEXT_COLOR,
                font=("Segoe UI", 14),
            )

    # ================= ANALYSIS =================

    def run_analysis_thread(self):
        if self.original_image is None:
            messagebox.showerror("Error", "Please load an image first.")
            return
        if self.current_image is None:
            messagebox.showerror("Error", "Current image is missing.")
            return
        t = threading.Thread(target=self.run_analysis, daemon=True)
        t.start()

    def run_analysis(self):
        try:
            ana_w, ana_h = 800, 800
            img_orig_small = self.original_image.copy()
            img_orig_small.thumbnail((ana_w, ana_h))

            img_edit_small = self.current_image.copy()
            img_edit_small.thumbnail((ana_w, ana_h))

            if img_orig_small.size != img_edit_small.size:
                img_edit_small = img_edit_small.resize(
                    img_orig_small.size, Image.Resampling.LANCZOS
                )

            edge_res = edges.analyze_edges(img_orig_small, img_edit_small)
            noise_res = noise.analyze_noise(img_orig_small, img_edit_small)
            hist_res = histogram.analyze_histogram(img_orig_small, img_edit_small)
            sharp_res = sharpness.analyze_sharpness(img_orig_small, img_edit_small)
            metric_res = metrics.analyze_metrics(img_orig_small, img_edit_small)
            art_comp = artifacts.detect_compression_artifacts(img_edit_small)
            art_smooth = artifacts.detect_oversmoothing(img_edit_small)

            self.root.after(
                0,
                lambda: self.update_analysis_ui(
                    edge_res,
                    noise_res,
                    hist_res,
                    sharp_res,
                    metric_res,
                    art_comp,
                    art_smooth,
                ),
            )
        except Exception as e:
            self.root.after(
                0,
                lambda: messagebox.showerror("Analysis Error", f"Analysis failed:\n{e}"),
            )

    def update_analysis_ui(
        self, edge_res, noise_res, hist_res, sharp_res, metric_res, art_comp, art_smooth
    ):
        # Store edge results for export
        self.analysis_results["edge"] = edge_res

        # Edge images
        w, h = getattr(self, "edge_target_size", (300, 200))
        self.tk_edge_orig = pil_to_tk(edge_res["orig_edge"], (w, h))
        self.img_edge_orig.config(image=self.tk_edge_orig)

        self.tk_edge_edit = pil_to_tk(edge_res["edited_edge"], (w, h))
        self.img_edge_edit.config(image=self.tk_edge_edit)

        self.tk_edge_diff = pil_to_tk(edge_res["difference_map"], (w, h))
        self.img_edge_diff.config(image=self.tk_edge_diff)

        self.lbl_edge_stats.config(
            text=f"Density Delta: {edge_res['density_delta']:.3f}"
        )

        # Noise
        self.txt_noise.delete("1.0", tk.END)
        self.txt_noise.insert(
            tk.END, f"Original Noise: {noise_res['noise_original']:.3f}\n"
        )
        self.txt_noise.insert(
            tk.END, f"Edited Noise:   {noise_res['noise_edited']:.3f}\n"
        )
        self.txt_noise.insert(
            tk.END, f"Delta:          {noise_res['noise_delta']:.3f}\n"
        )

        # Histogram text
        self.txt_hist.delete("1.0", tk.END)
        self.txt_hist.insert(
            tk.END, f"Brightness Delta: {hist_res['brightness_delta']:.2f}\n"
        )
        self.txt_hist.insert(
            tk.END, f"Contrast Delta:   {hist_res['contrast_delta']:.2f}\n"
        )

        # Hist plots
        self.tk_hist_orig = pil_to_tk(hist_res["plot_original"], (170, 100))
        self.lbl_hist_orig.config(image=self.tk_hist_orig)

        self.tk_hist_edit = pil_to_tk(hist_res["plot_edited"], (170, 100))
        self.lbl_hist_edit.config(image=self.tk_hist_edit)

        self.tk_hist_diff = pil_to_tk(hist_res["plot_diff"], (340, 100))
        self.lbl_hist_diff.config(image=self.tk_hist_diff)

        # Metrics
        self.txt_metrics.delete("1.0", tk.END)
        self.txt_metrics.insert(tk.END, f"MSE:  {metric_res['mse']:.2f}\n")
        self.txt_metrics.insert(tk.END, f"PSNR: {metric_res['psnr']:.2f} dB\n")
        self.txt_metrics.insert(tk.END, f"SSIM: {metric_res['ssim']:.4f}\n")
        self.txt_metrics.insert(tk.END, f"SNR (Orig): {metric_res['snr_orig']:.2f} dB\n")
        self.txt_metrics.insert(tk.END, f"SNR (Edit): {metric_res['snr_edit']:.2f} dB\n")
        self.txt_metrics.insert(
            tk.END, f"Entropy (Orig): {metric_res['entropy_orig']:.2f}\n"
        )
        self.txt_metrics.insert(
            tk.END, f"Entropy (Edit): {metric_res['entropy_edit']:.2f}\n"
        )

        # Artifacts
        self.txt_art.delete("1.0", tk.END)
        self.txt_art.insert(tk.END, f"Compression Score:   {art_comp:.2f}\n")
        self.txt_art.insert(tk.END, f"Oversmoothing Score: {art_smooth:.2f}\n")

        # Summary
        summary = report.generate_summary_text(
            edge_res,
            noise_res,
            hist_res,
            sharp_res,
            metric_data=metric_res,
            art_data={"compression": art_comp, "smoothing": art_smooth},
        )
        self.txt_summary.delete("1.0", tk.END)
        self.txt_summary.insert(tk.END, summary)

        # Hist plots for export
        self.current_hist_plots = {
            "original": hist_res["plot_original"],
            "edited": hist_res["plot_edited"],
            "diff": hist_res["plot_diff"],
            "combined": hist_res["plot_combined"],
        }

        messagebox.showinfo("Analysis Complete", "Analysis finished.")

    def save_histograms(self):
        if not hasattr(self, "current_hist_plots"):
            messagebox.showerror("Error", "Run analysis first!")
            return
        if "combined" not in self.current_hist_plots:
            messagebox.showerror(
                "Error", "Combined histogram not available. Please run analysis again."
            )
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")],
            title="Save Combined Histograms",
        )
        if not path:
            return
        try:
            self.current_hist_plots["combined"].save(path)
            messagebox.showinfo("Saved", f"Combined histograms saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save histograms: {e}")

    # ===== Export edge detection images =====

    def export_edge_detection(self):
        if "edge" not in self.analysis_results:
            messagebox.showerror(
                "Error", "Run analysis first to generate edge detection images."
            )
            return
        edge_res = self.analysis_results["edge"]
        export_dir = filedialog.askdirectory(
            title="Select Folder to Export Edge Images"
        )
        if not export_dir:
            return
        try:
            edge_res["orig_edge"].save(os.path.join(export_dir, "original_edges.png"))
            edge_res["edited_edge"].save(os.path.join(export_dir, "edited_edges.png"))
            edge_res["difference_map"].save(
                os.path.join(export_dir, "difference_edges.png")
            )
            messagebox.showinfo(
                "Exported",
                "Exported:\n"
                "- original_edges.png\n"
                "- edited_edges.png\n"
                "- difference_edges.png\n"
                f"\nTo:\n{export_dir}",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export edge images:\n{e}")

    def export_report(self):
        text = self.txt_summary.get("1.0", tk.END)
        path = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text File", "*.txt")]
        )
        if not path:
            return
        try:
            report.save_report_txt(text, path)
            messagebox.showinfo("Exported", f"Report saved to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report: {e}")

    # ========== FIXED MOBILE-STYLE CROP SYSTEM ==========

    def toggle_crop_mode(self):
        """Toggle crop mode on/off."""
        if not self.current_image:
            messagebox.showwarning("No Image", "Please load an image first.")
            return

        if self.crop_active:
            self.cancel_crop()
        else:
            self._activate_crop_mode()

    def _activate_crop_mode(self):
        """Activate crop mode with CropBox overlay."""
        self.crop_active = True

        # Clear any existing crop box
        if self.crop_box:
            try:
                self.crop_box.clear()
            except Exception:
                pass
            self.crop_box = None

        # Determine displayed image bounds on canvas (must match update_preview)
        w_canvas = self.canvas.winfo_width()
        h_canvas = self.canvas.winfo_height()
        img_w, img_h = self.current_image.size

        if img_w == 0 or img_h == 0 or w_canvas <= 1 or h_canvas <= 1:
            return

        scale = min(w_canvas / img_w, h_canvas / img_h)
        disp_w = int(img_w * scale)
        disp_h = int(img_h * scale)
        off_x = (w_canvas - disp_w) // 2
        off_y = (h_canvas - disp_h) // 2

        self._crop_scale = scale
        self._crop_bounds = (off_x, off_y, disp_w, disp_h)

        self.crop_box = CropBox(self.canvas, self._crop_bounds)
        self.crop_box.draw()

        # Mark crop button active if present
        if "crop" in self.transform_buttons:
            try:
                self.transform_buttons["crop"].set_active(True)
            except Exception:
                pass

        self._show_crop_buttons()

        # Override mouse bindings for crop interaction
        self.canvas.bind("<Button-1>", self._on_crop_click)
        self.canvas.bind("<B1-Motion>", self._on_crop_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_crop_release)

    def _show_crop_buttons(self):
        """Show ✓ Confirm / ✗ Cancel buttons in the preview header."""
        self._hide_crop_buttons()

        # header is the first child of center_panel
        header = self.center_panel.winfo_children()[0]
        self.crop_buttons_frame = ttk.Frame(header, style="Panel.TFrame")
        self.crop_buttons_frame.pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            self.crop_buttons_frame,
            text="✓ Confirm",
            width=10,
            command=self.confirm_crop,
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            self.crop_buttons_frame,
            text="✗ Cancel",
            width=10,
            command=self.cancel_crop,
        ).pack(side=tk.LEFT, padx=2)

    def _hide_crop_buttons(self):
        """Hide crop confirm/cancel buttons."""
        if self.crop_buttons_frame:
            try:
                self.crop_buttons_frame.destroy()
            except Exception:
                pass
            self.crop_buttons_frame = None

    def _on_crop_click(self, event):
        if not self.crop_active or not self.crop_box:
            return
        handle = self.crop_box.get_handle_at(event.x, event.y)
        if handle:
            self.crop_box.start_drag(event.x, event.y, handle)

    def _on_crop_drag(self, event):
        if not self.crop_active or not self.crop_box:
            return
        self.crop_box.update_drag(event.x, event.y)

    def _on_crop_release(self, event):
        if not self.crop_active or not self.crop_box:
            return
        self.crop_box.end_drag()

    def confirm_crop(self):
        """Apply crop to the underlying image and exit crop mode."""
        if not self.crop_active or not self.crop_box or not self.current_image:
            return

        # Crop rect in displayed image coordinates (pixels within disp_w x disp_h)
        rel_x, rel_y, crop_w, crop_h = self.crop_box.get_crop_rect()

        # Convert to original image coordinates using stored scale
        scale = getattr(self, "_crop_scale", None)
        if not scale or scale <= 0:
            self.cancel_crop()
            return

        img_w, img_h = self.current_image.size

        img_x0 = int(rel_x / scale)
        img_y0 = int(rel_y / scale)
        img_x1 = int((rel_x + crop_w) / scale)
        img_y1 = int((rel_y + crop_h) / scale)

        # Clamp
        img_x0 = max(0, min(img_x0, img_w - 1))
        img_y0 = max(0, min(img_y0, img_h - 1))
        img_x1 = max(img_x0 + 1, min(img_x1, img_w))
        img_y1 = max(img_y0 + 1, min(img_y1, img_h))

        if img_x1 - img_x0 < 5 or img_y1 - img_y0 < 5:
            messagebox.showwarning("Invalid Crop", "Crop area too small.")
            return

        try:
            cropped_img = self.current_image.crop((img_x0, img_y0, img_x1, img_y1))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to crop image: {e}")
            self.cancel_crop()
            return

        # After crop, treat cropped image as new original
        self.original_image = cropped_img
        self.current_image = cropped_img.copy()

        self.cancel_crop()
        self.reset_controls()
        self.update_preview()

    def cancel_crop(self):
        """Exit crop mode and restore normal behavior."""
        self.crop_active = False

        if self.crop_box:
            try:
                self.crop_box.clear()
            except Exception:
                pass
            self.crop_box = None

        self._hide_crop_buttons()

        if "crop" in self.transform_buttons:
            try:
                self.transform_buttons["crop"].set_active(False)
            except Exception:
                pass

        # Restore default mouse handlers
        try:
            self.canvas.bind("<Button-1>", self._default_canvas_bindings["<Button-1>"])
            self.canvas.bind(
                "<B1-Motion>", self._default_canvas_bindings["<B1-Motion>"]
            )
            self.canvas.bind(
                "<ButtonRelease-1>",
                self._default_canvas_bindings["<ButtonRelease-1>"],
            )
        except Exception:
            self.canvas.bind("<Button-1>", self.on_canvas_click)
            self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
            self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)


if __name__ == "__main__":
    root = tk.Tk()
    app = PyPicEditorApp(root)
    root.mainloop()
