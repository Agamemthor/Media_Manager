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

        if self.type == 'slideshow':
            self.create_content_frame_cell()
            self.media_manager.slideshow_manager.register_slideshow_cell(self.content_frame)
    
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
    
    def refresh_treeview(self):
        if self.type == 'media_tree':
            if self.treeview: 
                self.treeview.refresh()                         

    def create_content_frame_cell(self):     
        self.content_frame = ContentFrame(self.media_manager, self)

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
        self.grid_config = grid_config

        #initialize grid layout
        self.load_grid_from_config() 

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
                if cell.type == 'statusbar':
                    self.statusbar = cell.frame
                    break
        
        if self.statusbar:
            self.statusbar.status["text"] = status_text
            self.root.update_idletasks()

    def load_grid_from_config(self):
        uniform_row = self.grid_config['uniform_row']
        uniform_col = self.grid_config['uniform_col']

        for i in range(self.grid_config['grid_rows']):
            weight = self.grid_config['row_weights'][i]
            self.main_window.grid_rowconfigure(
                i,
                weight=weight,
                minsize=24,
                uniform=uniform_row,
                pad=0  # Remove row padding
            )
        for i in range(self.grid_config['grid_columns']):
            self.main_window.grid_columnconfigure(
                i,
                weight=self.grid_config['column_weights'][i],
                uniform=uniform_col,
                pad=0  # Remove column padding
            )

    def get_frame(self, row: int = 0, column: int = 0, rowspan: int = 1, columnspan: int = 1) -> tk.Frame:
        """Get a frame positioned at the specified grid location."""
        #Todo: check if frame already exists at this location and return it instead of creating a new one
        frame = tk.Frame(self.main_window,        
                            bd=0,               # Remove border
                            highlightthickness=0,  # Remove highlight
                            bg="black"          # Match background color (optional))
        )   
        frame.grid(
            row=row,
            column=column,
            rowspan=rowspan,
            columnspan=columnspan,
            sticky="nsew",
            padx=0,  # Remove horizontal padding
            pady=0   # Remove vertical padding
        )
        frame.grid_propagate(False)
        return frame
    
    def get_grid_cell_by_name(self, name: str) -> Optional[GridCell]:
        """Return the GridCell with the given name, or None if not found."""
        for cell in self.grid_cells:
            if cell.name == name:
                return cell
        return None
    
    def refresh_grids(self):
        for cell in self.grid_cells:
            if cell.type == 'media_tree':
                cell.treeview.refresh()
