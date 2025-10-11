# /app/classes/grid_manager.py
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Tuple, List
from .treeview_manager import TreeviewManager
from .content_frame import ContentFrame

class GridCell:
    def __init__(self,media_manager,grid_manager, frame: tk.Frame, type: str, name: str, linked_content_frame_name: str = ''):
        self.frame = frame
        self.frame.name = name
        self.name = name 
        self.type = type
        self.media_manager = media_manager
        self.statusbar = None
        self.linked_content_frame_name = None
        self.grid_manager = grid_manager
        
        if self.type == 'statusbar':
            self.statusbar = self.create_statusbar_cell()

        if self.type == 'content_frame':
            self.create_content_frame_cell()

        if self.type == 'media_tree':
            self.create_treeview_cell() 
            self.linked_content_frame_name = linked_content_frame_name        
    
    def create_content(self):     
        if self.type == 'media_tree':
            self.treeview.populate() 
            if self.linked_content_frame_name:
                grid_cell = self.grid_manager.get_grid_cell_by_name(self.linked_content_frame_name)
                if grid_cell:
                    content_frame = grid_cell.content_frame
                    if content_frame:
                        self.treeview.set_content_frame_cell(content_frame)
                grid_cell.frame.grid_propagate(False)
                self.frame.grid_propagate(False)



    def create_treeview_cell(self):
        self.treeview = TreeviewManager(self.media_manager, self.frame)   

    def create_content_frame_cell(self):     
        self.content_frame = ContentFrame(self.media_manager, self.frame)

    def create_statusbar_cell(self):
        # Add a status label to the status frame
        self.frame.status = ttk.Label(self.frame, text="Ready", anchor="w", relief="sunken")
        self.frame.status.pack(fill="x", padx=5, pady=2)

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
        self.statusbar = None

        # Set default or provided grid configuration
        self.grid_config = grid_config or {
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

        #initialize grid layout
        self.load_grid_from_config(self.grid_config) 

        #initialize grid cells
        for cell_config in self.grid_config['cell_configs']:
            self.update_grid_cell(cell_config)  

    def create_content(self):
        for cell in self.grid_cells:
            cell.create_content()

    def update_grid_cell(self, cell_config):
        type, name, row, column, rowspan, columnspan, linked_content_frame_name = cell_config
        frame = self.get_frame(row, column, rowspan, columnspan)
        grid_cell = GridCell(self.media_manager,self, frame, type, name, linked_content_frame_name)
        self.grid_cells.append(grid_cell)

    def set_status(self, status_text: str):
        if not self.statusbar:
            for cell in self.grid_cells:
                if cell.name == 'statusbar':
                    self.statusbar = cell.frame
                    break
        
        if self.statusbar:
            self.statusbar.status["text"] = status_text
            self.root.update_idletasks()

    def load_grid_from_config(self, grid_config: Dict):
        # Configure grid weights
        for i in range(self.grid_config['grid_rows']):
            weight = self.grid_config['row_weights'][i]
            self.main_window.grid_rowconfigure(i, weight=weight, minsize=24)

        for i in range(self.grid_config['grid_columns']):
            self.main_window.grid_columnconfigure(i, weight=self.grid_config['column_weights'][i])

    def get_frame(self, row: int = 0, column: int = 0, rowspan: int = 1, columnspan: int = 1) -> tk.Frame:
        """Get a frame positioned at the specified grid location."""
        #Todo: check if frame already exists at this location and return it instead of creating a new one
        frame = tk.Frame(self.main_window)
        frame.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, sticky="nsew")
        #@frame.grid_propagate(False)
        return frame
    
    def get_grid_cell_by_name(self, name: str) -> Optional[GridCell]:
        """Return the GridCell with the given name, or None if not found."""
        for cell in self.grid_cells:
            if cell.name == name:
                return cell
        return None

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