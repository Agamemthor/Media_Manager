# /app/classes/grid_manager.py
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Tuple, List

class GridCell:
    def __init__(self, frame: tk.Frame, name: str):
        self.frame = frame
        self.name = name

class GridManager:
    """
    A class to manage grid layouts in the application.
    Handles the main window grid 
    """
    def __init__(self, root: tk.Tk, grid_config: Dict = None):
        """
        Initialize the GridManager with the root window and grid configuration.

        Args:
            root: The root Tk window
            grid_config: Dictionary with grid configuration
        """
        self.root = root
        self.main_window = root
        self.grid_cells = list[GridCell] = []

        # Set default or provided grid configuration
        self.grid_config = grid_config or {
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

        for cell_config in grid_config['cell_configs']:
            self.update_grid_cell(cell_config)  

    def update_grid_cell(self, cell_config):
        row, column, rowspan, columnspan, name = cell_config

        frame = self.get_frame(row, column, rowspan, columnspan)
        frame.name = name  # Assign a name attribute to the frame

        if name == 'statusbar':
            # Add a status label to the status frame
            frame.status = ttk.Label(frame, text="Ready", anchor="w", relief="sunken")
            frame.status.pack(fill="x", padx=5, pady=2)

        if name == 'media_tree':
                

        if name == 'content_frame':
            pass


    def set_status(self, status_text: str):
        statusbar = self.get_frame_by_name('statusbar')
        if statusbar:
            statusbar.status["text"] = status_text
            self.root.update_idletasks()

    def load_grid_from_config(self, grid_config: Dict):
        # Configure grid weights
        for i in range(self.grid_config['rows']):
            self.main_window.grid_rowconfigure(i, weight=self.grid_config['row_weights'][i])

        for i in range(self.grid_config['columns']):
            self.main_window.grid_columnconfigure(i, weight=self.grid_config['column_weights'][i])

    def get_frame(self, row: int = 0, column: int = 0, rowspan: int = 1, columnspan: int = 1) -> tk.Frame:
        """
        Get a frame positioned at the specified grid location.

        Args:
            row: Row position
            column: Column position
            rowspan: Number of rows to span
            columnspan: Number of columns to span

        Returns:
            A frame configured for the specified grid location
        """
        #Todo: check if frame already exists at this location and return it instead of creating a new one
        frame = tk.Frame(self.main_window)
        frame.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, sticky="nsew")
        return frame



        # Get frame for the treeview (left side, first row)
        #self.treeview_frame = self.grid_manager.get_frame(row=0, column=0)

        # Get empty frame for the right side (first row)
        #self.content_frame = self.grid_manager.get_frame(row=0, column=1)

        # Create an image frame inside the content frame
        #self.image_frame = tk.Frame(self.content_frame)
        #self.image_frame.pack(fill="both", expand=True)
        # Initialize ImageManager
        #self.image_manager = ImageManager(self.image_frame)

        # Initialize Treeview in the left frame
        #self.tree = ttk.Treeview(self.treeview_frame)
        #self.tree.pack(side="left", fill="both", expand=True)

        # Initialize TreeviewManager
        #self.treeview_manager = TreeviewManager(self.tree, self.image_manager)
        #self.treeview_manager.multi_slideshow_manager = self.multi_slideshow_manager

        # Add a scrollbar to the treeview
        #scrollbar = ttk.Scrollbar(self.treeview_frame, orient="vertical", command=self.tree.yview)
        #scrollbar.pack(side="right", fill="y")
        #self.tree.configure(yscrollcommand=scrollbar.set)

        # Create a status bar frame that spans both columns in the second row
        #self.status_frame = self.grid_manager.get_frame(row=1, column=0, columnspan=2)

        # Add a status label to the status frame
        #self.status = ttk.Label(self.status_frame, text="Ready", anchor="w", relief="sunken")
        #self.status.pack(fill="x", padx=5, pady=2)

        #self.treeview_manager.populate(self.media_manager)