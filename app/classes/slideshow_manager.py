# /app/classes/slideshow_manager.py
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional
from PIL import Image, ImageTk
import os
import random
from .media_file import MediaFile
from .content_frame import ContentFrame
import random

class SlideshowCell:
    def __init__(self, content_frame: ContentFrame):
        self.slideshow_cell_id = content_frame.grid_cell.name
        self.media_list = []
        self.content_frame = content_frame
        self.image_index = 0
        self.current_media = None

    def preload_media(self):
        # Get the media file at the current index.
        if self.media_list:
            self.current_media = self.media_list[self.image_index]
            self.content_frame.preload_media_file(self.current_media)
            # Increment the index, wrapping around to 0 if necessary
            self.image_index = (self.image_index + 1) % len(self.media_list)
    
    def show_preloaded_media(self):
        if self.media_list:
            self.content_frame.show_preloaded_media(self.current_media)
            
    def show_next_image(self):
        # Get the media file at the current index.
        if self.media_list:
            media_file = self.media_list[self.image_index]
            # Display the media file
            self.content_frame.display_media(media_file)
            # Increment the index, wrapping around to 0 if necessary
            self.image_index = (self.image_index + 1) % len(self.media_list)

class MultiSlideshow:
    """
    A class to manage a window with multiple slideshows in a grid layout.
    This class is responsible for scheduling all image changes.
    """

    def __init__(self, media_manager):
        """        Initialize the MultiSlideshow with image files.        """
        # Create the slideshow window
        self.media_manager = media_manager

        self.slideshow_cells = []  # List to hold all slideshow cells

        # Scheduling variables
        self.delay = 8000  # 8 seconds between images
        self.cell_indices = []  # Track index for each cell
        self.random = True
        self.is_running = False
        self.after_id = None
        self.first_update = True  # Flag for first update
        self.media_file_list = []


    def _start_slideshows(self, media_file_list):
        """Start all slideshows after the window is visible and sized."""
        if not self.is_running:
            self.is_running = True
            if self.first_update:
                # Add a small delay for the first update to ensure proper sizing
                self.first_update = False

                for cell in self.slideshow_cells:
                    if self.random:
                        _media_file_list = media_file_list.copy()
                        random.shuffle(_media_file_list)
                    cell.media_list = _media_file_list
                self.media_manager.root.after(500, self._update_all_cells)
            else:
                self._update_all_cells()

    def _update_all_cells(self):
        """Update all cells with new random images."""
        if not self.is_running:
            return

        # Update each cell with a new random image
        for cell in self.slideshow_cells:
            cell.preload_media()

        for cell in self.slideshow_cells:
            cell.show_preloaded_media()

        # Schedule the next update
        self.after_id = self.media_manager.root.after(self.delay, self._update_all_cells)

    def register_slideshow_cell(self, content_frame: ContentFrame):
        slideshow_cell = SlideshowCell(content_frame)
        self.slideshow_cells.append(slideshow_cell)