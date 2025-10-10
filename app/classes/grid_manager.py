# /app/classes/grid_manager.py
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Tuple, List

class GridManager:
    """
    A class to manage grid layouts in the application.
    Handles the main window grid and creation of new windows.
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
        self.sub_windows: Dict[str, tk.Toplevel] = {}  # Track sub-windows by name

        # Set default or provided grid configuration
        self.grid_config = grid_config or {
            'rows': 1,
            'columns': 2,
            'row_weights': [1],
            'column_weights': [1, 1]  # Default 30% left, 70% right
        }

        # Initialize the main window grid
        self._initialize_main_grid()

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

    def _initialize_main_grid(self):
        """Initialize the main window grid based on configuration"""
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
        frame = tk.Frame(self.main_window)
        frame.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, sticky="nsew")
        return frame

    def create_new_window(self, title: str, size: Tuple[int, int] = (800, 600)) -> tk.Toplevel:
        """
        Create a new sub-window.

        Args:
            title: The title for the new window
            size: The size of the new window (width, height)

        Returns:
            The newly created Toplevel window#json string 
        """
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry(f"{size[0]}x{size[1]}")
        self.sub_windows[title] = window
        return window

    def get_window_by_name(self, name: str) -> Optional[tk.Toplevel]:
        """
        Get a sub-window by its name.

        Args:
            name: The title/name of the window

        Returns:
            The Toplevel window if found, None otherwise
        """
        return self.sub_windows.get(name)

    def close_window(self, name: str) -> bool:
        """
        Close a sub-window by its name.

        Args:
            name: The title/name of the window

        Returns:
            True if the window was found and closed, False otherwise
        """
        window = self.sub_windows.get(name)
        if window:
            window.destroy()
            del self.sub_windows[name]
            return True
        return False

    def close_all_windows(self):
        """Close all sub-windows"""
        for name, window in list(self.sub_windows.items()):
            window.destroy()
            del self.sub_windows[name]

    def update_grid(self, rows: int = None, columns: int = None,
                   row_weights: List[int] = None,
                   column_weights: List[int] = None):
        """
        Update the main window grid configuration.

        Args:
            rows: Number of rows (optional)
            columns: Number of columns (optional)
            row_weights: List of row weights (optional)
            column_weights: List of column weights (optional)
        """
        if rows is not None:
            self.grid_config['rows'] = rows
        if columns is not None:
            self.grid_config['columns'] = columns
        if row_weights is not None:
            self.grid_config['row_weights'] = row_weights
        if column_weights is not None:
            self.grid_config['column_weights'] = column_weights

        # Reconfigure the grid
        for i in range(self.grid_config['rows']):
            self.main_window.grid_rowconfigure(i, weight=self.grid_config['row_weights'][i])

        for i in range(self.grid_config['columns']):
            self.main_window.grid_columnconfigure(i, weight=self.grid_config['column_weights'][i])
