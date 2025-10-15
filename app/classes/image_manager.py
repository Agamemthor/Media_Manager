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
        self.preloaded_image: Optional[Image.Image] = None

        # Create a placeholder label
        self._create_placeholder()

        # Bind to frame resize events
        self.frame.bind("<Configure>", self._on_frame_resize)

    def _create_placeholder(self):
        if self.current_image_label:
            self.current_image_label.destroy()
        self.current_image_label = ttk.Label(
            self.frame,
            text="Select an image file to preview",
            borderwidth=0,      # Remove border
            relief="flat",      # No relief
            anchor="center",
            background='black'  # Match frame background
        )
        self.current_image_label.place(relx=0, rely=0, anchor="center")
        self.current_image_label.pack(fill="both", expand=True, padx=0, pady=0)

    def preload_image(self, file_path: str):

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
            self._get_scaled_image()

        except Exception as e:
            print(f"Error loading image: {e}")
            self._create_placeholder()
            if self.on_image_error:
                self.on_image_error(str(e))

    def _get_scaled_image(self):

        # Get current frame dimensions
        frame_width = self.frame.winfo_width()
        frame_height = self.frame.winfo_height()

        # Minimum dimensions to prevent tiny images
        min_width, min_height = 100, 100
        display_width = max(frame_width - 5, min_width)
        display_height = max(frame_height - 5, min_height)

        # Scale image to fit while maintaining aspect ratio
        width, height = self.current_pil_image.size
        ratio = min(display_width/width, display_height/height)
        new_size = (int(width * ratio), int(height * ratio))

        # Resize the image
        resized_image = self.current_pil_image.resize(new_size, Image.LANCZOS)

        # Convert to PhotoImage
        self.preloaded_image = ImageTk.PhotoImage(resized_image)
    
    def display_preloaded_image(self):
        # Update the label
        if not self.current_image_label:
            self.current_image_label = ttk.Label(self.frame)
            self.current_image_label.pack(fill="both", expand=True)

        self.current_image_label.configure(image=self.preloaded_image)
        self.current_image_label.image = self.preloaded_image  # Keep a reference

    def _on_frame_resize(self, event):
        """Handle frame resize events"""
        if self.current_pil_image and self.current_image_path:
            #self._display_scaled_image()
            self.preload_image(self.current_image_path)
            self.display_preloaded_image()

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
