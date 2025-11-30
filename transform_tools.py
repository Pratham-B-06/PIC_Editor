import tkinter as tk
from tkinter import ttk

class CircularButton(tk.Canvas):
    def __init__(self, parent, size=60, icon_text="?", label_text="Label", command=None, bg_color="#353535", hover_color="#ff9b00", text_color="#e6e6e6", parent_bg="#2a2a2a"):
        super().__init__(parent, width=size, height=size + 20, bg=parent_bg, highlightthickness=0)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.size = size
        self.is_active = False  # Track active state
        
        # Draw Circle
        pad = 4
        self.circle = self.create_oval(pad, pad, size-pad, size-pad, fill=bg_color, outline="")
        
        # Draw Icon
        self.icon = self.create_text(size/2, size/2, text=icon_text, fill=text_color, font=("Segoe UI Symbol", 16, "bold"))
        
        # Draw Label
        self.label = self.create_text(size/2, size + 10, text=label_text, fill=text_color, font=("Segoe UI", 8))
        
        # Bind events
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        
        # Bind to items as well
        self.tag_bind(self.circle, "<Button-1>", self.on_click)
        self.tag_bind(self.icon, "<Button-1>", self.on_click)
        self.tag_bind(self.circle, "<Enter>", self.on_enter)
        self.tag_bind(self.icon, "<Enter>", self.on_enter)
        self.tag_bind(self.label, "<Button-1>", self.on_click)
        self.tag_bind(self.label, "<Enter>", self.on_enter)
        
    def on_enter(self, event):
        if not self.is_active:  # Only change on hover if not active
            self.itemconfig(self.circle, fill=self.hover_color)
            self.itemconfig(self.icon, fill="#121212") # Dark icon on bright bg
        
    def on_leave(self, event):
        if not self.is_active:  # Only revert if not active
            self.itemconfig(self.circle, fill=self.bg_color)
            self.itemconfig(self.icon, fill=self.text_color)
        
    def on_click(self, event):
        if self.command:
            self.command()

    def set_active(self, is_active):
        self.is_active = is_active
        if is_active:
            self.itemconfig(self.circle, fill=self.hover_color)
            self.itemconfig(self.icon, fill="#121212")
        else:
            self.itemconfig(self.circle, fill=self.bg_color)
            self.itemconfig(self.icon, fill=self.text_color)

def create_transform_tools(parent, app):
    container = ttk.Frame(parent, style="Panel.TFrame")
    
    # Header
    header_frame = ttk.Frame(container, style="Panel.TFrame")
    header_frame.pack(fill=tk.X, pady=(10, 5), padx=10)
    ttk.Label(header_frame, text="Transform Tools", style="Header.TLabel").pack(side=tk.LEFT)
    
    # Reset Button (Small text button)
    lbl_reset = ttk.Label(header_frame, text="↺ Reset", style="Muted.TLabel", cursor="hand2")
    lbl_reset.pack(side=tk.RIGHT)
    lbl_reset.bind("<Button-1>", lambda e: app.reset_controls())
    
    # Grid for buttons
    grid_frame = ttk.Frame(container, style="Panel.TFrame")
    grid_frame.pack(fill=tk.X, padx=5)
    
    # Helper to create buttons
    app.transform_buttons = {}
    
    def make_btn(row, col, icon, label, cmd, key=None):
        # We assume panel color is #2a2a2a based on main.py
        btn = CircularButton(grid_frame, icon_text=icon, label_text=label, command=cmd, parent_bg="#2a2a2a")
        btn.grid(row=row, column=col, padx=5, pady=5)
        if key:
            app.transform_buttons[key] = btn
        return btn
        
    # Row 1
    # Rotate, Crop
    make_btn(0, 0, "↻", "Rotate", lambda: show_slider_panel(app, "rotate"))
    make_btn(0, 1, "✂", "Crop", lambda: app.toggle_crop_mode(), key='crop')
    
    # Row 2
    # Vertical, Horizontal
    make_btn(1, 0, "↕", "Vertical", lambda: show_slider_panel(app, "skew_y"))
    make_btn(1, 1, "↔", "Horizontal", lambda: show_slider_panel(app, "skew_x"))
    
    # Slider Panel (Hidden by default)
    app.transform_slider_frame = ttk.Frame(container, style="Panel.TFrame")
    app.transform_slider_frame.pack(fill=tk.X, padx=10, pady=5)
    
    # Label header
    label_header = ttk.Frame(app.transform_slider_frame, style="Panel.TFrame")
    label_header.pack(fill=tk.X)
    
    app.transform_slider_label = ttk.Label(label_header, text="Value")
    app.transform_slider_label.pack(side=tk.LEFT)
    
    app.transform_slider_value = ttk.Label(label_header, text="0", style="Muted.TLabel")
    app.transform_slider_value.pack(side=tk.RIGHT)
    
    app.transform_scale = ttk.Scale(app.transform_slider_frame, from_=-180, to=180, command=lambda v: on_transform_slider(app, v))
    app.transform_scale.pack(fill=tk.X)
    
    # Close slider button
    ttk.Button(app.transform_slider_frame, text="Done", command=lambda: hide_slider_panel(app)).pack(pady=2)
    
    # Initially hide
    app.transform_slider_frame.pack_forget()
    
    return container

def show_slider_panel(app, mode):
    # Hide first to reset
    app.transform_slider_frame.pack_forget()
    
    app.current_transform_mode = mode
    
    # Configure scale based on mode
    if mode == "rotate":
        app.transform_slider_label.config(text="Rotate Angle")
        app.transform_scale.configure(from_=-180, to=180)
        current_val = app.edit_state.get('rotate', 0)
        app.transform_scale.set(current_val)
        app.transform_slider_value.config(text=f"{int(current_val)}°")
        

    elif mode == "skew_x":
        app.transform_slider_label.config(text="Horizontal Skew")
        app.transform_scale.configure(from_=-45, to=45)
        current_val = app.edit_state.get('skew_x', 0)
        app.transform_scale.set(current_val)
        app.transform_slider_value.config(text=f"{int(current_val)}°")
        
    elif mode == "skew_y":
        app.transform_slider_label.config(text="Vertical Skew")
        app.transform_scale.configure(from_=-45, to=45)
        current_val = app.edit_state.get('skew_y', 0)
        app.transform_scale.set(current_val)
        app.transform_slider_value.config(text=f"{int(current_val)}°")
        
    app.transform_slider_frame.pack(fill=tk.X, padx=10, pady=5)

def hide_slider_panel(app):
    app.transform_slider_frame.pack_forget()
    app.current_transform_mode = None

def on_transform_slider(app, value):
    if not hasattr(app, 'current_transform_mode') or not app.current_transform_mode:
        return
        
    mode = app.current_transform_mode
    val = float(value)
    
    if mode == "rotate":
        app.edit_state['rotate'] = val
        app.transform_slider_value.config(text=f"{int(val)}°")

    elif mode == "skew_x":
        app.edit_state['skew_x'] = val
        app.transform_slider_value.config(text=f"{int(val)}°")
    elif mode == "skew_y":
        app.edit_state['skew_y'] = val
        app.transform_slider_value.config(text=f"{int(val)}°")
        
    app.apply_pipeline()
