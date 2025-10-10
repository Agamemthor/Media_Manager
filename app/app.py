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
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        #Get rootfolder from db or prompt for one
        self.rootfolder = self.get_rootfolder()
        self.root.title(self.rootfolder)

        # Initialize Mediamanager with 2x2 grid (1 row for content, 1 row for status bar)
        window_config = {
            'height': 600,
            'width': 800,  
            'show_taskbar': True,
            'title': "Media Manager",
            'show_menubar': True,
            'show_statusbar': True,
            'fullscreen': False,
            'grid_rows': 2,  # 2 rows: 1 for content, 1 for status bar
            'grid_columns': 2,
            'row_weights': [1, 0],  # First row expands, second row fixed height
            'column_weights': [1, 3],  # Equal column weights
            'cell_configs': { #row, column, rowspan, columnspan, name
                (0,0,1,1, 'media_tree'), 
                (0,1,1,1, 'content_frame'), 
                (1,0,2,1, 'statusbar')
            }
        }

        self.media_manager = MediaManager(db_manager, window_config)

if __name__ == "__main__": 
    try:
        conn_config = {
            'dbname': 'media_manager',
            'user': 'youruser',
            'password': 'yourpassword',
            'host': 'localhost',
            'port': "5432",
            'retries': 5,
            'delay': 3
        }
        app = MediaManagerApp(DBManager(conn_config))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {e}")

