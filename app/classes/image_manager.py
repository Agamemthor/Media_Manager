# /app/classes/image_manager.py
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from PIL import Image, ImageTk
import os

class ImageManager:
    """
    A class to manage image display in the application.
    Shows images that scale to fit the available frame space.
    """

    def __init__(self, frame: tk.Frame):
        """
        Initialize the ImageManager with a frame to display images.

        Args:
            frame: The frame where images will be displayed
        """
        self.frame = frame
        self.current_image_label: Optional[ttk.Label] = None
        self.current_image_path: Optional[str] = None
        self.on_image_error: Optional[Callable] = None
        self.current_pil_image: Optional[Image.Image] = None  # Store the PIL image

        # Create a placeholder label
        self._create_placeholder()

        # Bind to frame resize events
        self.frame.bind("<Configure>", self._on_frame_resize)

    def _create_placeholder(self):
        """Create a placeholder label when no image is displayed"""
        if self.current_image_label:
            self.current_image_label.destroy()

        self.current_image_label = ttk.Label(
            self.frame,
            text="Select an image file to preview",
            relief="groove",
            anchor="center"
        )
        self.current_image_label.place(relx=0.5, rely=0.5, anchor="center")
        #self.current_image_label.pack(fill="both", expand=True)

    def display_image(self, file_path: str):
        """
        Display an image in the frame, scaled to fit the available space.

        Args:
            file_path: Path to the image file
        """
        # Early return if the path is the same as the current image
        if self.current_image_path == file_path:
            return

        # Check if file exists
        if not os.path.exists(file_path):
            self._create_placeholder()
            if self.on_image_error:
                self.on_image_error("File not found")
            return

        try:
            # Open the image
            pil_image = Image.open(file_path)
            self.current_pil_image = pil_image
            self.current_image_path = file_path

            # Display the image with current frame dimensions
            self._display_scaled_image()

        except Exception as e:
            print(f"Error loading image: {e}")
            self._create_placeholder()
            if self.on_image_error:
                self.on_image_error(str(e))

    def _display_scaled_image(self):
        if not self.current_pil_image or not self.current_image_path:
            return

        try:
            frame_width = self.frame.winfo_width()
            frame_height = self.frame.winfo_height()
            min_width, min_height = 100, 100
            display_width = max(frame_width - 20, min_width)
            display_height = max(frame_height - 20, min_height)

            if hasattr(self, '_last_image_cache'):
                last_path, last_size = self._last_image_cache
                if last_path == self.current_image_path and last_size == (display_width, display_height):
                    return
            self._last_image_cache = (self.current_image_path, (display_width, display_height))

            # Always resize (upscale or downscale) to fill the cell
            img = self.current_pil_image.copy()
            width, height = img.size
            ratio = min(display_width / width, display_height / height)
            new_size = (int(width * ratio), int(height * ratio))
            resized_image = img.resize(new_size, Image.LANCZOS)

            tk_image = ImageTk.PhotoImage(resized_image)
            if not self.current_image_label:
                self.current_image_label = ttk.Label(self.frame)
                self.current_image_label.place(relx=0.5, rely=0.5, anchor="center")

            self.current_image_label.configure(image=tk_image)
            self.current_image_label.image = tk_image

        except Exception as e:
            print(f"Error displaying scaled image: {e}")
            self._create_placeholder()

    def _on_frame_resize(self, event):
        """Handle frame resize events"""
        if self.current_pil_image and self.current_image_path:
            self._display_scaled_image()

    def clear(self):
        """Clear the current image display"""
        self._create_placeholder()
        self.current_image_path = None
        self.current_pil_image = None

    def refresh(self):
        """Refresh the current image (useful when frame size changes)"""
        if self.current_image_path:
            self.display_image(self.current_image_path)

    def set_error_handler(self, callback: Callable):
        """Set a callback for image loading errors"""
        self.on_image_error = callback
