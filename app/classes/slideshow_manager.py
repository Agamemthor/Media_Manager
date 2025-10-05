# /app/classes/slideshow_manager.py
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional
from PIL import Image, ImageTk
import os
import random
from .media_file import MediaFile

class SlideshowCell:
    """
    A class to manage a single cell in the slideshow grid.
    Each cell displays images but doesn't manage timing.
    """
    def __init__(self, parent_frame: tk.Frame):
        """
        Initialize the SlideshowCell with a parent frame.

        Args:
            parent_frame: The frame where this cell will display images
        """
        self.parent_frame = parent_frame
        self.current_image_label = None
        self._create_image_label()

        # Wait for the frame to be properly sized
        self.parent_frame.bind("<Configure>", self._on_frame_configure)

    def _on_frame_configure(self, event=None):
        """Handle frame resize events."""
        # This ensures the label fills the frame when it's resized
        if self.current_image_label:
            self.current_image_label.pack_forget()
            self.current_image_label.pack(fill="both", expand=True)

    def _create_image_label(self):
        """Create a label for displaying images."""
        if self.current_image_label:
            self.current_image_label.destroy()

        self.current_image_label = tk.Label(self.parent_frame, bg='black')
        self.current_image_label.pack(fill="both", expand=True)

    def display_image(self, image_path: str):
        """
        Display an image in this cell.

        Args:
            image_path: Path to the image file to display
        """
        try:
            # Open the image
            pil_image = Image.open(image_path)

            # Get frame dimensions - ensure we have valid dimensions
            frame_width = self.parent_frame.winfo_width()
            frame_height = self.parent_frame.winfo_height()

            # If dimensions are too small (like 1x1), use a default size
            if frame_width <= 1 or frame_height <= 1:
                frame_width = 400  # Default width
                frame_height = 300  # Default height

            # Minimum dimensions to prevent tiny images
            min_width, min_height = 100, 100
            display_width = max(frame_width - 20, min_width)
            display_height = max(frame_height - 20, min_height)

            # Scale image to fit while maintaining aspect ratio
            width, height = pil_image.size
            ratio = min(display_width/width, display_height/height)
            new_size = (int(width * ratio), int(height * ratio))

            # Resize the image
            resized_image = pil_image.resize(new_size, Image.LANCZOS)

            # Convert to PhotoImage
            tk_image = ImageTk.PhotoImage(resized_image)

            # Update the label
            if self.current_image_label:
                self.current_image_label.configure(image=tk_image)
                self.current_image_label.image = tk_image  # Keep a reference

        except Exception as e:
            print(f"Error loading image: {e}")
            # Clear the label if there's an error
            if self.current_image_label:
                self.current_image_label.configure(image='')
                self.current_image_label.image = None

    def clear(self):
        """Clear the current image display."""
        if self.current_image_label:
            self.current_image_label.configure(image='')
            self.current_image_label.image = None

class MultiSlideshowWindow:
    """
    A class to manage a window with multiple slideshows in a grid layout.
    This class is responsible for scheduling all image changes.
    """

    def __init__(self, image_files: List[MediaFile]):
        """
        Initialize the MultiSlideshowWindow with image files.

        Args:
            image_files: List of MediaFile objects to display across all slideshows
        """
        # Create the slideshow window
        self.slideshow_window = tk.Toplevel()
        self.slideshow_window.title("Multi-Slideshow")

        # First make the window visible and set to fullscreen
        self.slideshow_window.update_idletasks()  # Process all pending events
        self.slideshow_window.attributes('-fullscreen', True)

        # Store and filter image files
        self.all_image_files = [
            f for f in image_files
            if f.media_type.lower() in ["image", "gif", "jpg", "jpeg", "png", "bmp", "tiff"]
        ]

        if not self.all_image_files:
            messagebox.showwarning("Warning", "No image files to display.")
            self.slideshow_window.destroy()
            return

        # Grid configuration
        self.rows = 2
        self.cols = 4
        self.slideshow_cells = []  # List to hold all slideshow cells

        # Create the grid and cells
        self._create_grid()

        # Bind escape key to close
        self.slideshow_window.bind("<Escape>", lambda e: self.close())

        # Scheduling variables
        self.delay = 8000  # 8 seconds between images
        self.cell_indices = []  # Track index for each cell
        self.is_running = False
        self.after_id = None
        self.first_update = True  # Flag for first update

        # Initialize random indices for each cell
        for _ in range(self.rows * self.cols):
            self.cell_indices.append(random.randint(0, len(self.all_image_files) - 1))

        # Start slideshows when window is visible and properly sized
        self.slideshow_window.bind("<Visibility>", self._on_window_visible)

    def _on_window_visible(self, event=None):
        """Handle window visibility event."""
        # Add a small delay to ensure the window is properly sized
        # This helps prevent the first images from being too small
        self.slideshow_window.after(500, self._start_slideshows)

    def _create_grid(self):
        """Create the grid layout for slideshows."""
        # Configure grid weights
        for i in range(self.rows):
            self.slideshow_window.grid_rowconfigure(i, weight=1)
        for j in range(self.cols):
            self.slideshow_window.grid_columnconfigure(j, weight=1)

        # Create slideshow cells in a grid
        for row in range(self.rows):
            for col in range(self.cols):
                # Create a frame for each cell
                cell_frame = tk.Frame(self.slideshow_window, bg='black')
                cell_frame.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)

                # Create a slideshow cell for this frame
                cell = SlideshowCell(cell_frame)
                self.slideshow_cells.append(cell)

    def _start_slideshows(self):
        """Start all slideshows after the window is visible and sized."""
        if not self.is_running:
            self.is_running = True
            if self.first_update:
                # Add a small delay for the first update to ensure proper sizing
                self.first_update = False
                self.slideshow_window.after(500, self._update_all_cells)
            else:
                self._update_all_cells()

    def _update_all_cells(self):
        """Update all cells with new random images."""
        if not self.is_running:
            return

        # Update each cell with a new random image
        for i, cell in enumerate(self.slideshow_cells):
            if self.all_image_files:
                # Get a random image for this cell
                self.cell_indices[i] = random.randint(0, len(self.all_image_files) - 1)
                media_file = self.all_image_files[self.cell_indices[i]]
                full_path = os.path.join(media_file.folder_path, media_file.file_name)
                cell.display_image(full_path)

        # Schedule the next update
        self.after_id = self.slideshow_window.after(self.delay, self._update_all_cells)

    def close(self):
        """Close the slideshow window."""
        self.is_running = False
        if self.after_id:
            self.slideshow_window.after_cancel(self.after_id)

        # Clear all cells
        for cell in self.slideshow_cells:
            cell.clear()

        # Destroy the window
        self.slideshow_window.destroy()
