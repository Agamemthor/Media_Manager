# /app/classes/grid_manager.py
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Tuple, List
from .treeview_manager import TreeviewManager
from .content_frame import ContentFrame

class GridCell:
    def __init__(self,media_manager, frame: tk.Frame, name: str):
        self.frame = frame
        self.frame.name = name
        self.name = name 
        self.media_manager = media_manager
        
        if name == 'statusbar':
            self.statusbar = self.create_statusbar_cell()
    
    def create_content_cell(self):        

        if self.name == 'media_tree':
            self.create_treeview_cell()                

        if self.name == 'content_frame':
            self.content_frame = ContentFrame(self.media_manager, self.frame)

    def create_treeview_cell(self):
        self.treeview = TreeviewManager(self.media_manager, self.frame)   
        self.treeview.populate()

    def create_statusbar_cell(self):
        # Add a status label to the status frame
        self.frame.status = ttk.Label(self.frame, text="Ready", anchor="w", relief="sunken")
        self.frame.status.pack(fill="x", padx=5, pady=2)
        self.frame.configure(height=24)
        self.frame.grid_propagate(False)


class GridManager:
    """
    A class to manage grid layouts in the application.
    Handles the main window grid 
    """
    def __init__(self, media_manager, root: tk.Tk, grid_config: Dict = None):
        """Initialize the GridManager with the root window and grid configuration."""
        self.root = root
        self.main_window = root
        self.grid_cells: List[GridCell] = []
        self.media_manager = media_manager

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

        for cell_config in self.grid_config['cell_configs']:
            self.update_grid_cell(cell_config)  

    def create_content_cells(self):
        for cell in self.grid_cells:
            cell.create_content_cell()

    def update_grid_cell(self, cell_config):
        row, column, rowspan, columnspan, name = cell_config
        grid_cell = GridCell(self.media_manager,self.get_frame(row, column, rowspan, columnspan), name)
        self.grid_cells.append(grid_cell)

    def set_status(self, status_text: str):
        statusbar = self.get_frame_by_name('statusbar')
        if statusbar:
            statusbar.status["text"] = status_text
            self.root.update_idletasks()

    def load_grid_from_config(self, grid_config: Dict):
        # Configure grid weights
        for i in range(self.grid_config['grid_rows']):
            self.main_window.grid_rowconfigure(i, weight=self.grid_config['row_weights'][i])

        for i in range(self.grid_config['grid_columns']):
            self.main_window.grid_columnconfigure(i, weight=self.grid_config['column_weights'][i])

    def get_frame(self, row: int = 0, column: int = 0, rowspan: int = 1, columnspan: int = 1) -> tk.Frame:
        """Get a frame positioned at the specified grid location."""
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



        #self.treeview_manager.populate(self.media_manager)