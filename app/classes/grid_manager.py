import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional
import logging
from .treeview_manager import TreeviewManager
from .content_frame import ContentFrame

logger = logging.getLogger(__name__)

class GridCell:
    def __init__(
        self,
        media_manager,
        grid_manager,
        frame: tk.Frame,
        cell_config: Dict,
    ):
        self.frame = frame
        self.frame.name = cell_config.get("name", "")
        self.name = cell_config.get("name", "")
        self.type = cell_config.get("type", "")
        self.media_manager = media_manager
        self.statusbar = None
        self.linked_content_frame_name = cell_config.get("linked_content_frame_name", "")
        self.grid_manager = grid_manager
        self.cell_config = cell_config
        
        if self.type == "statusbar":
            self.statusbar = self.create_statusbar_cell()
        if self.type == "content_frame":
            self.create_content_frame_cell()
        if self.type == "media_tree":
            self.create_treeview_cell()
        if self.type == "slideshow":
            self.create_content_frame_cell()
            self.media_manager.slideshow_manager.register_slideshow_cell(self.content_frame)

    def create_content(self):
        """Create content for the grid cell."""
        if self.type == "media_tree":
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
        """Create a treeview cell."""
        self.treeview = TreeviewManager(self, self.media_manager, self.frame)

    def refresh_treeview(self):
        """Refresh the treeview."""
        if self.type == "media_tree" and self.treeview:
            self.treeview.refresh()

    def create_content_frame_cell(self):
        """Create a content frame cell."""
        self.content_frame = ContentFrame(self.media_manager, self)

    def create_statusbar_cell(self):
        """Create a statusbar cell."""
        self.frame.status = ttk.Label(
            self.frame,
            text=self.cell_config.get("status_text", "Ready"),
            anchor=self.cell_config.get("status_anchor", "w"),
            relief=self.cell_config.get("status_relief", "sunken")
        )
        self.frame.status.pack(
            fill=self.cell_config.get("status_fill", "x"),
            padx=self.cell_config.get("status_padx", 5),
            pady=self.cell_config.get("status_pady", 2)
        )

class GridManager:
    """Manages grid layouts in the application."""

    def __init__(self, media_manager, root: tk.Tk, grid_config: Dict = None):
        """Initialize the GridManager with the root window and grid configuration."""
        self.root = root
        self.main_window = root
        self.grid_cells: List[GridCell] = []
        self.media_manager = media_manager
        self.statusbar = None
        self.grid_config = grid_config
        self.load_grid_from_config()
        for cell_config in self.grid_config.get("cell_configs", []):
            self.update_grid_cell(cell_config)

    def create_content(self):
        """Create content for all grid cells."""
        for cell in self.grid_cells:
            cell.create_content()

    def update_grid_cell(self, cell_config: Dict):
        """Update a grid cell."""
        frame = self.get_frame(cell_config)
        grid_cell = GridCell(
            self.media_manager,
            self,
            frame,
            cell_config
        )
        self.grid_cells.append(grid_cell)

    def set_status(self, status_text: str):
        """Set the status text."""
        if not self.statusbar:
            for cell in self.grid_cells:
                if cell.type == "statusbar":
                    self.statusbar = cell.frame
                    break

        if self.statusbar:
            self.statusbar.status["text"] = status_text
            self.root.update_idletasks()

    def load_grid_from_config(self):
        """Load grid configuration."""
        uniform_row = self.grid_config.get("uniform_row", "")
        uniform_col = self.grid_config.get("uniform_col", "")
        row_weights = self.grid_config.get("row_weights", [1, 0])
        column_weights = self.grid_config.get("column_weights", [1, 3])
        row_minsize = self.grid_config.get("row_minsize", [0, 0])
        col_minsize = self.grid_config.get("col_minsize", [0, 0])

        for i in range(self.grid_config.get("grid_rows", 2)):
            weight = row_weights[i] if i < len(row_weights) else 1
            minsize = row_minsize[i] if i < len(row_minsize) else 0
            self.main_window.grid_rowconfigure(
                i,
                weight=weight,
                minsize=minsize,
                uniform=uniform_row,
                pad=self.grid_config.get("row_pad", 0)
            )

        for i in range(self.grid_config.get("grid_columns", 2)):
            weight = column_weights[i] if i < len(column_weights) else 1
            minsize = col_minsize[i] if i < len(col_minsize) else 0
            self.main_window.grid_columnconfigure(
                i,
                weight=weight,
                minsize=minsize,
                uniform=uniform_col,
                pad=self.grid_config.get("column_pad", 0)
            )

    def get_frame(self, cell_config: Dict) -> tk.Frame:
        """Get a frame positioned at the specified grid location."""
        frame = tk.Frame(
            self.main_window,
            bd=cell_config.get("bd", 0),
            highlightthickness=cell_config.get("highlightthickness", 0),
            bg=cell_config.get("bg", "black"),
        )
        frame.grid(
            row=cell_config.get("row", 0),
            column=cell_config.get("column", 0),
            rowspan=cell_config.get("rowspan", 1),
            columnspan=cell_config.get("columnspan", 1),
            sticky=cell_config.get("sticky", "nsew"),
            padx=cell_config.get("padx", 0),
            pady=cell_config.get("pady", 0),
        )
        frame.grid_propagate(cell_config.get("grid_propagate", False))
        return frame

    def get_grid_cell_by_name(self, name: str) -> Optional["GridCell"]:
        """Return the GridCell with the given name, or None if not found."""
        for cell in self.grid_cells:
            if cell.name == name:
                return cell
        return None

    def refresh_grids(self):
        """Refresh all grids."""
        for cell in self.grid_cells:
            if cell.type == "media_tree":
                cell.treeview.refresh()
