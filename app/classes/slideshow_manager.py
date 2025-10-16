import tkinter as tk
from tkinter import messagebox
from typing import List, Optional
from PIL import Image, ImageTk
import os
import random
import logging
from .media_file import MediaFile
from .content_frame import ContentFrame

logger = logging.getLogger(__name__)

class SlideshowCell:
    def __init__(self, content_frame: ContentFrame):
        self.slideshow_cell_id = content_frame.grid_cell.name
        self.media_list = []
        self.content_frame = content_frame
        self.image_index = 0
        self.current_media = None

    def preload_media(self):
        """Preload media."""
        if self.media_list:
            self.current_media = self.media_list[self.image_index]
            self.content_frame.preload_media_file(self.current_media)
            self.image_index = (self.image_index + 1) % len(self.media_list)

    def show_preloaded_media(self):
        """Show preloaded media."""
        if self.media_list:
            self.content_frame.show_preloaded_media(self.current_media)

    def show_next_image(self):
        """Show the next image."""
        if self.media_list:
            media_file = self.media_list[self.image_index]
            self.content_frame.display_media(media_file)
            self.image_index = (self.image_index + 1) % len(self.media_list)

class MultiSlideshow:
    """Manages a window with multiple slideshows in a grid layout."""

    def __init__(self, media_manager):
        """Initialize the MultiSlideshow with image files."""
        self.media_manager = media_manager
        self.slideshow_cells = []
        self.delay = 8000
        self.cell_indices = []
        self.random = True
        self.is_running = False
        self.after_id = None
        self.first_update = True
        self.media_file_list = []

    def _start_slideshows(self, media_file_list: List[MediaFile]):
        """Start all slideshows after the window is visible and sized."""
        if not self.is_running:
            self.is_running = True
            if self.first_update:
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
        for cell in self.slideshow_cells:
            cell.preload_media()
        for cell in self.slideshow_cells:
            cell.show_preloaded_media()
        self.after_id = self.media_manager.root.after(self.delay, self._update_all_cells)

    def register_slideshow_cell(self, content_frame: ContentFrame):
        """Register a slideshow cell."""
        slideshow_cell = SlideshowCell(content_frame)
        self.slideshow_cells.append(slideshow_cell)
