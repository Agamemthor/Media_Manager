import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor
import platform
import subprocess
from PIL import Image
from dataclasses import dataclass, field 
from typing import Dict, List, Tuple, Optional
from classes import DBManager, MediaFile, MediaFolder, MediaManager, TreeviewManager, GridManager, ImageManager, MultiSlideshowWindow

class MediaManagerApp:
    def __init__(self):
        conn_config = {
            'dbname': 'media_manager',
            'user': 'youruser',
            'password': 'yourpassword',
            'host': 'localhost',
            'port': "5432",
            'retries': 5,
            'delay': 3
        }
        # Initialize Mediamanager with 2x2 grid (1 row for content, 1 row for status bar)
        window_config = {
            'height': 600,
            'width': 800,
            'borderless': False, #the overrideredirect parameter is a fickle beast. Ignores the always_on_top parameter and app is always on top of everything
            'show_custom_titlebar': False,
            'title': "Media Manager",
            'show_menubar': False,
            'fullscreen': False, # does not work when borderless is True
            'always_on_top': False, # if borderless = true, app is always on top
            'exit_on_escape': True,  # does not work if borderless is True
            'fullscreen_on_f11': True,  # does not work if borderless is True
        }        
        grid_config = {
            'grid_rows': 2,  # 2 rows: 1 for content, 1 for status bar
            'grid_columns': 2,
            'row_weights': [1, 0],  # First row expands, second row fixed height
            'column_weights': [1, 3],  # Equal column weights
            'cell_configs': { #type, name, row, column, rowspan, columnspan, linked_content_frame_name
                ('media_tree', 'media_tree_1', 0, 0, 1, 1, 'content_frame_1'),
                ('content_frame', 'content_frame_1', 0, 1, 1, 1, ''),
                ('statusbar', 'statusbar_1', 1, 0, 1, 2, '')
            }
        }

        self.media_manager = MediaManager(conn_config, window_config, grid_config)

if __name__ == "__main__": 
    #try:

    app = MediaManagerApp()
    app.media_manager.root.mainloop()
    #except Exception as e:
        #messagebox.showerror("Error", f"Failed to start application: {e}")

