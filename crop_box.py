"""
Mobile-style crop box with adjustable handles.
Provides an interactive crop rectangle with 8 resize handles and drag-to-move functionality.
"""

class CropBox:
    """
    Interactive crop box with 8 handles (4 corners + 4 sides) for resizing.
    Can be moved by dragging the interior.
    """
    
    def __init__(self, canvas, image_bounds, initial_rect=None):
        """
        Initialize crop box.
        
        Args:
            canvas: tkinter Canvas widget
            image_bounds: (x, y, width, height) of the image area
            initial_rect: Optional (x, y, w, h) for initial crop box
        """
        self.canvas = canvas
        self.img_x, self.img_y, self.img_w, self.img_h = image_bounds
        
        # Crop box dimensions (in canvas coordinates)
        if initial_rect:
            self.x, self.y, self.width, self.height = initial_rect
        else:
            # Center crop box at 70% of image size
            self.width = int(self.img_w * 0.7)
            self.height = int(self.img_h * 0.7)
            self.x = self.img_x + (self.img_w - self.width) // 2
            self.y = self.img_y + (self.img_h - self.height) // 2
        
        # Drag state
        self.active_handle = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_start_rect = (0, 0, 0, 0)
        
        # Canvas items
        self.overlay_items = []
        self.box_items = []
        self.handle_items = {}
        
        # Handle size
        self.handle_size = 12
        self.min_size = 20
        
        # Colors
        self.box_color = "#FFFFFF"
        self.handle_color = "#FF9B00"
        self.overlay_color = "#000000"
        self.overlay_alpha = 0.5
        
    def draw(self):
        """Draw the crop box, handles, and overlay."""
        self.clear()
        
        # Draw semi-transparent overlay outside crop box
        self._draw_overlay()
        
        # Draw crop box rectangle
        box_id = self.canvas.create_rectangle(
            self.x, self.y,
            self.x + self.width, self.y + self.height,
            outline=self.box_color,
            width=2,
            tags="cropbox"
        )
        self.box_items.append(box_id)
        
        # Draw grid lines (rule of thirds)
        self._draw_grid()
        
        # Draw 8 handles
        self._draw_handles()
        
    def _draw_overlay(self):
        """Draw semi-transparent overlay outside crop box."""
        # Top overlay
        if self.y > self.img_y:
            overlay = self.canvas.create_rectangle(
                self.img_x, self.img_y,
                self.img_x + self.img_w, self.y,
                fill=self.overlay_color,
                stipple="gray50",
                outline="",
                tags="crop_overlay"
            )
            self.overlay_items.append(overlay)
        
        # Bottom overlay
        if self.y + self.height < self.img_y + self.img_h:
            overlay = self.canvas.create_rectangle(
                self.img_x, self.y + self.height,
                self.img_x + self.img_w, self.img_y + self.img_h,
                fill=self.overlay_color,
                stipple="gray50",
                outline="",
                tags="crop_overlay"
            )
            self.overlay_items.append(overlay)
        
        # Left overlay
        if self.x > self.img_x:
            overlay = self.canvas.create_rectangle(
                self.img_x, self.y,
                self.x, self.y + self.height,
                fill=self.overlay_color,
                stipple="gray50",
                outline="",
                tags="crop_overlay"
            )
            self.overlay_items.append(overlay)
        
        # Right overlay
        if self.x + self.width < self.img_x + self.img_w:
            overlay = self.canvas.create_rectangle(
                self.x + self.width, self.y,
                self.img_x + self.img_w, self.y + self.height,
                fill=self.overlay_color,
                stipple="gray50",
                outline="",
                tags="crop_overlay"
            )
            self.overlay_items.append(overlay)
    
    def _draw_grid(self):
        """Draw rule of thirds grid lines."""
        # Vertical lines
        x1 = self.x + self.width // 3
        x2 = self.x + 2 * self.width // 3
        
        line1 = self.canvas.create_line(
            x1, self.y, x1, self.y + self.height,
            fill=self.box_color, width=1, dash=(4, 4), tags="cropbox"
        )
        line2 = self.canvas.create_line(
            x2, self.y, x2, self.y + self.height,
            fill=self.box_color, width=1, dash=(4, 4), tags="cropbox"
        )
        self.box_items.extend([line1, line2])
        
        # Horizontal lines
        y1 = self.y + self.height // 3
        y2 = self.y + 2 * self.height // 3
        
        line3 = self.canvas.create_line(
            self.x, y1, self.x + self.width, y1,
            fill=self.box_color, width=1, dash=(4, 4), tags="cropbox"
        )
        line4 = self.canvas.create_line(
            self.x, y2, self.x + self.width, y2,
            fill=self.box_color, width=1, dash=(4, 4), tags="cropbox"
        )
        self.box_items.extend([line3, line4])
    
    def _draw_handles(self):
        """Draw 8 resize handles."""
        hs = self.handle_size
        
        # Corner handles
        handles = {
            'nw': (self.x, self.y),
            'ne': (self.x + self.width, self.y),
            'sw': (self.x, self.y + self.height),
            'se': (self.x + self.width, self.y + self.height),
            # Side handles
            'n': (self.x + self.width // 2, self.y),
            's': (self.x + self.width // 2, self.y + self.height),
            'w': (self.x, self.y + self.height // 2),
            'e': (self.x + self.width, self.y + self.height // 2),
        }
        
        for handle_name, (hx, hy) in handles.items():
            handle = self.canvas.create_rectangle(
                hx - hs // 2, hy - hs // 2,
                hx + hs // 2, hy + hs // 2,
                fill=self.handle_color,
                outline=self.box_color,
                width=2,
                tags=f"crop_handle_{handle_name}"
            )
            self.handle_items[handle_name] = handle
    
    def get_handle_at(self, x, y):
        """
        Detect which handle or area was clicked.
        
        Returns:
            'nw', 'ne', 'sw', 'se', 'n', 's', 'e', 'w', 'move', or None
        """
        hs = self.handle_size
        
        # Check corner handles first
        handles = {
            'nw': (self.x, self.y),
            'ne': (self.x + self.width, self.y),
            'sw': (self.x, self.y + self.height),
            'se': (self.x + self.width, self.y + self.height),
            'n': (self.x + self.width // 2, self.y),
            's': (self.x + self.width // 2, self.y + self.height),
            'w': (self.x, self.y + self.height // 2),
            'e': (self.x + self.width, self.y + self.height // 2),
        }
        
        for handle_name, (hx, hy) in handles.items():
            if abs(x - hx) <= hs and abs(y - hy) <= hs:
                return handle_name
        
        # Check if inside crop box (for moving)
        if (self.x <= x <= self.x + self.width and 
            self.y <= y <= self.y + self.height):
            return 'move'
        
        return None
    
    def start_drag(self, x, y, handle):
        """Start dragging operation."""
        self.active_handle = handle
        self.drag_start_x = x
        self.drag_start_y = y
        self.drag_start_rect = (self.x, self.y, self.width, self.height)
        
        # Change cursor based on handle
        cursor_map = {
            'nw': 'top_left_corner',
            'ne': 'top_right_corner',
            'sw': 'bottom_left_corner',
            'se': 'bottom_right_corner',
            'n': 'top_side',
            's': 'bottom_side',
            'w': 'left_side',
            'e': 'right_side',
            'move': 'fleur'
        }
        cursor = cursor_map.get(handle, 'arrow')
        self.canvas.config(cursor=cursor)
    
    def update_drag(self, x, y):
        """Update crop box during drag."""
        if not self.active_handle:
            return
        
        dx = x - self.drag_start_x
        dy = y - self.drag_start_y
        
        start_x, start_y, start_w, start_h = self.drag_start_rect
        
        if self.active_handle == 'move':
            # Move entire box
            self.x = start_x + dx
            self.y = start_y + dy
            self._constrain_to_bounds()
            
        elif self.active_handle == 'nw':
            # Resize from top-left corner
            self.x = start_x + dx
            self.y = start_y + dy
            self.width = start_w - dx
            self.height = start_h - dy
            self._constrain_resize()
            
        elif self.active_handle == 'ne':
            # Resize from top-right corner
            self.y = start_y + dy
            self.width = start_w + dx
            self.height = start_h - dy
            self._constrain_resize()
            
        elif self.active_handle == 'sw':
            # Resize from bottom-left corner
            self.x = start_x + dx
            self.width = start_w - dx
            self.height = start_h + dy
            self._constrain_resize()
            
        elif self.active_handle == 'se':
            # Resize from bottom-right corner
            self.width = start_w + dx
            self.height = start_h + dy
            self._constrain_resize()
            
        elif self.active_handle == 'n':
            # Resize from top
            self.y = start_y + dy
            self.height = start_h - dy
            self._constrain_resize()
            
        elif self.active_handle == 's':
            # Resize from bottom
            self.height = start_h + dy
            self._constrain_resize()
            
        elif self.active_handle == 'w':
            # Resize from left
            self.x = start_x + dx
            self.width = start_w - dx
            self._constrain_resize()
            
        elif self.active_handle == 'e':
            # Resize from right
            self.width = start_w + dx
            self._constrain_resize()
        
        self.draw()
    
    def _constrain_to_bounds(self):
        """Keep crop box within image bounds."""
        # Constrain x
        if self.x < self.img_x:
            self.x = self.img_x
        if self.x + self.width > self.img_x + self.img_w:
            self.x = self.img_x + self.img_w - self.width
        
        # Constrain y
        if self.y < self.img_y:
            self.y = self.img_y
        if self.y + self.height > self.img_y + self.img_h:
            self.y = self.img_y + self.img_h - self.height
    
    def _constrain_resize(self):
        """Constrain resize to minimum size and image bounds."""
        # Enforce minimum size
        if self.width < self.min_size:
            if self.active_handle in ['nw', 'w', 'sw']:
                self.x = self.x + self.width - self.min_size
            self.width = self.min_size
        
        if self.height < self.min_size:
            if self.active_handle in ['nw', 'n', 'ne']:
                self.y = self.y + self.height - self.min_size
            self.height = self.min_size
        
        # Constrain to image bounds
        if self.x < self.img_x:
            self.width += self.x - self.img_x
            self.x = self.img_x
        
        if self.y < self.img_y:
            self.height += self.y - self.img_y
            self.y = self.img_y
        
        if self.x + self.width > self.img_x + self.img_w:
            self.width = self.img_x + self.img_w - self.x
        
        if self.y + self.height > self.img_y + self.img_h:
            self.height = self.img_y + self.img_h - self.y
    
    def end_drag(self):
        """End dragging operation."""
        self.active_handle = None
        self.canvas.config(cursor="")
    
    def get_crop_rect(self):
        """
        Get crop rectangle in image coordinates.
        
        Returns:
            (x, y, width, height) relative to image
        """
        # Convert from canvas coordinates to image-relative coordinates
        rel_x = self.x - self.img_x
        rel_y = self.y - self.img_y
        return (rel_x, rel_y, self.width, self.height)
    
    def clear(self):
        """Remove all crop box elements from canvas."""
        for item in self.overlay_items + self.box_items + list(self.handle_items.values()):
            self.canvas.delete(item)
        
        self.overlay_items = []
        self.box_items = []
        self.handle_items = {}
