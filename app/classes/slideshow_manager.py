# /app/classes/slideshow_manager.py
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional
from PIL import Image, ImageTk
import os
import random
from .media_file import MediaFile

class SlideshowManager:
    """
    A class to manage a single slideshow in a grid cell.
    Each instance manages its own image display.
    """

    def __init__(self, parent_frame: tk.Frame):
        """
        Initialize the SlideshowManager with a parent frame.

        Args:
            parent_frame: The frame where this slideshow will be displayed
        """
        self.parent_frame = parent_frame
        self.image_files: List[MediaFile] = []
        self.current_index = 0
        self.delay = 8000  # 8 seconds between images
        self.is_running = False
        self.after_id = None
        self.current_image_label = None

        # Create a label for displaying images
        self._create_image_label()

    def _create_image_label(self):
        """Create a label for displaying images."""
        if self.current_image_label:
            self.current_image_label.destroy()

        self.current_image_label = tk.Label(self.parent_frame, bg='black')
        self.current_image_label.pack(fill="both", expand=True)

    def start_slideshow(self, image_files: List[MediaFile]):
        """
        Start a slideshow with the given list of image files.

        Args:
            image_files: List of MediaFile objects to display in the slideshow
        """
        # Filter to only include image files
        self.image_files = [
            f for f in image_files
            if f.media_type.lower() in ["image", "gif", "jpg", "jpeg", "png", "bmp", "tiff"]
        ]

        if not self.image_files:
            return

        # Shuffle the images for variety
        random.shuffle(self.image_files)
        self.current_index = 0
        self.is_running = True
        self._show_next_image()

    def _show_next_image(self):
        """Show the next image in the slideshow."""
        if not self.is_running or not self.image_files:
            return

        # Get the next image
        media_file = self.image_files[self.current_index]
        full_path = os.path.join(media_file.folder_path, media_file.file_name)

        try:
            # Open the image
            pil_image = Image.open(full_path)

            # Get frame dimensions
            frame_width = self.parent_frame.winfo_width()
            frame_height = self.parent_frame.winfo_height()

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

            # Convert to PhotoImage - create a new one for this frame
            tk_image = ImageTk.PhotoImage(resized_image)

            # Update the label
            if self.current_image_label:
                self.current_image_label.configure(image=tk_image)
                self.current_image_label.image = tk_image  # Keep a reference
            else:
                self._create_image_label()
                self.current_image_label.configure(image=tk_image)
                self.current_image_label.image = tk_image  # Keep a reference

            # Update the index
            self.current_index = (self.current_index + 1) % len(self.image_files)

            # Schedule the next image
            if self.is_running:
                self.after_id = self.parent_frame.after(self.delay, self._show_next_image)

        except Exception as e:
            print(f"Error loading image: {e}")
            # Try the next image
            self.current_index = (self.current_index + 1) % len(self.image_files)
            if self.is_running:
                self.after_id = self.parent_frame.after(100, self._show_next_image)  # Try again soon

    def stop_slideshow(self):
        """Stop the slideshow."""
        self.is_running = False
        if self.after_id:
            self.parent_frame.after_cancel(self.after_id)
            self.after_id = None

        if self.current_image_label:
            self.current_image_label.configure(image='')
            self.current_image_label.image = None

class MultiSlideshowWindow:
    """
    A class to manage a window with multiple slideshows in a grid layout.
    """

    def __init__(self, image_files: List[MediaFile]):
        """
        Initialize the MultiSlideshowWindow with image files.

        Args:
            image_files: List of MediaFile objects to display across all slideshows
        """
        self.slideshow_window = tk.Toplevel()
        self.slideshow_window.title("Multi-Slideshow")
        self.slideshow_window.attributes('-fullscreen', True)  # Start in fullscreen

        # Store image files
        self.image_files = image_files

        # Create grid layout
        self.rows = 2
        self.cols = 4
        self.slideshow_managers = []  # List to hold all slideshow managers

        # Create the grid
        self._create_grid()

        # Add a close button
        close_button = tk.Button(
            self.slideshow_window,
            text="Close (Esc)",
            command=self.close
        )
        #close_button.pack(pady=10)

        # Bind escape key to close
        self.slideshow_window.bind("<Escape>", lambda e: self.close())

        # Start slideshows when window is visible
        self.slideshow_window.bind("<Visibility>", self._start_slideshows)

    def _create_grid(self):
        """Create the grid layout for slideshows."""
        # Configure grid weights
        for i in range(self.rows):
            self.slideshow_window.grid_rowconfigure(i, weight=1)
        for j in range(self.cols):
            self.slideshow_window.grid_columnconfigure(j, weight=1)

        # Create slideshow managers in a grid
        for row in range(self.rows):
            for col in range(self.cols):
                # Create a frame for each slideshow
                cell_frame = tk.Frame(self.slideshow_window, bg='black')
                cell_frame.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)

                # Create a slideshow manager for this cell
                slideshow_manager = SlideshowManager(cell_frame)
                self.slideshow_managers.append(slideshow_manager)

    def _start_slideshows(self, event=None):
        """Start all slideshows when the window becomes visible."""
        if not self.image_files:
            messagebox.showwarning("Warning", "No image files to display.")
            return

        # Start each slideshow with the same image files
        # Each slideshow will shuffle the files differently
        for manager in self.slideshow_managers:
            manager.start_slideshow(self.image_files.copy())

    def close(self):
        """Close the slideshow window."""
        # Stop all slideshows
        for manager in self.slideshow_managers:
            manager.stop_slideshow()

        # Destroy the window
        self.slideshow_window.destroy()
