import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from PIL import Image, ImageTk
import os
import logging

logger = logging.getLogger(__name__)

class ImageManager:
    """Manages image display in the application."""

    def __init__(self, frame: tk.Frame):
        """Initialize the ImageManager with a frame to display images."""
        self.frame = frame
        self.current_image_label: Optional[ttk.Label] = None
        self.current_image_path: Optional[str] = None
        self.on_image_error: Optional[Callable] = None
        self.current_pil_image: Optional[Image.Image] = None
        self.preloaded_image: Optional[Image.Image] = None
        self._create_placeholder()
        self.frame.bind("<Configure>", self._on_frame_resize)

    def _create_placeholder(self):
        """Create a placeholder label."""
        if self.current_image_label:
            self.current_image_label.destroy()
        self.current_image_label = ttk.Label(
            self.frame,
            text="Select an image file to preview",
            borderwidth=0,
            relief="flat",
            anchor="center",
            background="black",
        )
        self.current_image_label.place(relx=0, rely=0, anchor="center")
        self.current_image_label.pack(fill="both", expand=True, padx=0, pady=0)

    def preload_image(self, file_path: str):
        """Preload an image."""
        if not os.path.exists(file_path):
            self._create_placeholder()
            if self.on_image_error:
                self.on_image_error("File not found")
            return
        try:
            pil_image = Image.open(file_path)
            self.current_pil_image = pil_image
            self.current_image_path = file_path
            self._get_scaled_image()
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            self._create_placeholder()
            if self.on_image_error:
                self.on_image_error(str(e))

    def _get_scaled_image(self):
        """Get a scaled image."""
        frame_width = self.frame.winfo_width()
        frame_height = self.frame.winfo_height()
        min_width, min_height = 100, 100
        display_width = max(frame_width - 5, min_width)
        display_height = max(frame_height - 5, min_height)
        width, height = self.current_pil_image.size
        ratio = min(display_width / width, display_height / height)
        new_size = (int(width * ratio), int(height * ratio))
        resized_image = self.current_pil_image.resize(new_size, Image.LANCZOS)
        self.preloaded_image = ImageTk.PhotoImage(resized_image)

    def display_preloaded_image(self):
        """Display the preloaded image."""
        if not self.current_image_label:
            self.current_image_label = ttk.Label(self.frame)
            self.current_image_label.pack(fill="both", expand=True)
        self.current_image_label.configure(image=self.preloaded_image)
        self.current_image_label.image = self.preloaded_image

    def _on_frame_resize(self, event):
        """Handle frame resize events."""
        if self.current_pil_image and self.current_image_path:
            self.preload_image(self.current_image_path)
            self.display_preloaded_image()

    def clear(self):
        """Clear the current image display."""
        self._create_placeholder()
        self.current_image_path = None
        self.current_pil_image = None

    def refresh(self):
        """Refresh the current image."""
        if self.current_image_path:
            self.display_image(self.current_image_path)

    def set_error_handler(self, callback: Callable):
        """Set a callback for image loading errors."""
        self.on_image_error = callback
