# /app/classes/slideshow_manager.py
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional
from PIL import Image, ImageTk
import os
import random
from .media_file import MediaFile
from .content_frame import ContentFrame

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
                self.media_file_list = media_file_list
                self.slideshow_window.after(500, self._update_all_cells)
            else:
                self._update_all_cells()

    def _update_all_cells(self):
        """Update all cells with new random images."""
        if not self.is_running:
            return

        # Update each cell with a new random image
        for i, cell in enumerate(self.slideshow_cells):
            if self.media_file_list:
                # Get a random image for this cell
                self.cell_indices[i] = random.randint(0, len(self.media_file_list) - 1)
                media_file = self.media_file_list[self.cell_indices[i]]
                full_path = os.path.join(media_file.folder_path, media_file.file_name)
                cell.display_image(full_path)

        # Schedule the next update
        self.after_id = self.slideshow_window.after(self.delay, self._update_all_cells)

    def register_slideshow_cell(self, content_frame: ContentFrame):
        self.slideshow_cells.append(content_frame)

    def start_slideshow_preset_2x4_img(self, media_list: list[MediaFile]):        
        window_config = {
            'height': 600,
            'width': 800,
            'borderless': False, #the overrideredirect parameter is a fickle beast. Ignores the always_on_top parameter and app is always on top of everything
            'show_custom_titlebar': False,
            'title': "Media Manager",
            'show_menubar': False,
            'fullscreen': True, # does not work when borderless is True
            'always_on_top': False, # if borderless = true, app is always on top
            'exit_on_escape': True,  # does not work if borderless is True
            'fullscreen_on_f11': True,  # does not work if borderless is True
        }        
        grid_config = {
            'grid_rows': 2,
            'grid_columns': 4,
            'row_weights': [1, 1],
            'column_weights': [1, 1, 1, 1],
            'cell_configs': { #type, name, row, column, rowspan, columnspan, linked_content_frame_name
                # Row 0
                ('slideshow', 'slideshow_1', 0, 0, 1, 1, ''),
                ('slideshow', 'slideshow_2', 0, 1, 1, 1, ''),
                ('slideshow', 'slideshow_3', 0, 2, 1, 1, ''),
                ('slideshow', 'slideshow_4', 0, 3, 1, 1, ''),
                # Row 1
                ('slideshow', 'slideshow_5', 1, 0, 1, 1, ''),
                ('slideshow', 'slideshow_6', 1, 1, 1, 1, ''),
                ('slideshow', 'slideshow_7', 1, 2, 1, 1, ''),
                ('slideshow', 'slideshow_8', 1, 3, 1, 1, ''),
            }
        }
        self.media_manager.start_new_media_manager(self.media_manager.db_manager.conn_config, window_config, grid_config, media_list)
        
