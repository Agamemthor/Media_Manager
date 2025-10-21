import tkinter as tk
from tkinter import ttk
from tkinter.ttk import Style

from typing import Dict, List, Optional
import logging
from .treeview_manager import TreeviewManager
from .content_frame import ContentFrame

logger = logging.getLogger(__name__)

class WindowComponent:
    def __init__(
        self,
        media_manager,
        grid_manager,
        frame: tk.Frame,
        cell_config: Dict,
        parent
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
        self.parent = parent
        
        if self.type == "statusbar":
            self.statusbar = self.create_statusbar_cell()
        if self.type == "content_frame":
            self.create_content_frame_cell()
        if self.type == "media_tree":
            self.create_treeview_cell()
        if self.type == "grid":
            self.create_grid()
        if self.type == "slideshow":
            if self.parent and isinstance(self.parent, WindowComponent) and self.parent.type == 'grid':
                self.create_window_component()
            self.create_content_frame_cell()
            self.media_manager.slideshow_manager.register_slideshow_cell(self.content_frame)

    def create_window_component(self):
        self.frame.grid(
            row=self.cell_config.get("row", 0),
            column=self.cell_config.get("column", 0),
            rowspan=self.cell_config.get("rowspan", 1),
            columnspan=self.cell_config.get("columnspan", 1),
            sticky=self.cell_config.get("sticky", "nsew"),
            padx=self.cell_config.get("padx", 0),
            pady=self.cell_config.get("pady", 0),
        )

        self.frame.grid_propagate(self.cell_config.get("grid_propagate", False))

    def create_grid(self):
        uniform_row = self.cell_config.get("uniform_row", "")
        uniform_col = self.cell_config.get("uniform_col", "")
        row_weights = self.cell_config.get("row_weights", [1, 0])
        column_weights = self.cell_config.get("column_weights", [1, 3])
        row_minsize = self.cell_config.get("row_minsize", [0, 0])
        col_minsize = self.cell_config.get("col_minsize", [0, 0])

        for i in range(self.cell_config.get("grid_rows", 2)):
            weight = row_weights[i] if i < len(row_weights) else 1
            minsize = row_minsize[i] if i < len(row_minsize) else 0
            self.frame.grid_rowconfigure(
                i,
                weight=weight,
                minsize=minsize,
                uniform=uniform_row,
                pad=self.cell_config.get("row_pad", 0)
            )

        for i in range(self.cell_config.get("grid_columns", 2)):
            weight = column_weights[i] if i < len(column_weights) else 1
            minsize = col_minsize[i] if i < len(col_minsize) else 0
            self.frame.grid_columnconfigure(
                i,
                weight=weight,
                minsize=minsize,
                uniform=uniform_col,
                pad=self.cell_config.get("column_pad", 0)
            )

    def create_content(self):
        """Create content for the grid cell."""
        if self.type == "media_tree":
            self.treeview.populate()
            if self.linked_content_frame_name:
                window_component = self.grid_manager.get_window_component_by_name(self.linked_content_frame_name)
                if window_component:
                    content_frame = window_component.content_frame
                    if content_frame:
                        self.treeview.set_content_frame_cell(content_frame)
                window_component.frame.grid_propagate(False)
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

class WindowComponentManager:
    """Manages grid layouts in the application."""

    def __init__(self, media_manager, root: tk.Tk, grid_config: Dict = None):
        """Initialize the WindowComponentManager with the root window and grid configuration."""
        self.root = root
        self.window_components: List[WindowComponent] = []
        self.paned_windows: List[ttk.PanedWindow] = []
        self.media_manager = media_manager
        self.statusbar = None
        self.grid_config = grid_config
        self.load_grid_from_config()

    def create_content(self):
        """Create content for all grid cells."""
        for cell in self.window_components:
            cell.create_content()

    def set_status(self, status_text: str):
        """Set the status text."""
        if not self.statusbar:
            for cell in self.window_components:
                if cell.type == "statusbar":
                    self.statusbar = cell.frame
                    break

        if self.statusbar:
            self.statusbar.status["text"] = status_text
            self.root.update_idletasks()

    def load_grid_from_config(self):
        """Load grid configuration."""
        cell_config = self.grid_config.get("cell_configs", [])
        self.load_cell_from_config(cell_config, self.root)

        
    def load_cell_from_config(self, cell_configs, parent):
        """
        Recursive function to load cell_configs from the config.json
        I liked the idea to have a nested structure in the json config, relations are very explicit that way.
        We want flexibility in how we manage grids and paned_windows, including them in the cell_config  should make sense.
        But it feels a little wrong. Perhaps if we had included frames in json hierarchy things would be more explicit. Oh well.
        INPUT:
        - cell_configs: a list of one or more cell_config
        - parent: can be self.root, PanedWindow, or WindowComponent
        """
        for cell_config in cell_configs:
            newborn_object = None # we create paned_window or window_component
            newborn_frame = None # make sure we pass paned_window or window_component.frame
            type = cell_config.get('type', '')

            if type == 'paned_window':
                #paned_windows are directly added to self.root or another paned_window
                paned_window = self.get_paned_window(parent = parent, cell_config = cell_config)
                self.paned_windows.append(paned_window)
                newborn_object = paned_window
                newborn_frame = paned_window
            else: 
                if parent and isinstance(parent, (tk.Tk, tk.Toplevel, ttk.Panedwindow)):
                    root = parent
                elif parent and isinstance(parent, WindowComponent): 
                    root = parent.frame
                else:
                    raise 'bleh'

                frame = self.get_frame(root, cell_config)
                window_component = WindowComponent(
                    frame=frame,
                    media_manager=self.media_manager, 
                    grid_manager=self, 
                    cell_config=cell_config,
                    parent= parent
                    )
                self.window_components.append(window_component)
                newborn_object = window_component
                newborn_frame = window_component.frame            

            pack_config = cell_config.get('pack', {})
            if pack_config:
                newborn_frame.pack(
                    fill = pack_config.get('fill', 'both'),
                    expand = pack_config.get('expand', True),
                    padx = pack_config.get('padx', 0),
                    pady = pack_config.get('pady', 0)
                    )
                
            #check for child_configs and process them first before proceeding
            child_cell_config = cell_config.get("cell_configs", [])
            if child_cell_config:
                self.load_cell_from_config(child_cell_config, newborn_object)

            if parent and isinstance(parent, ttk.Panedwindow):
                parent.add(newborn_frame, weight=cell_config.get("weight", 0))


    def get_paned_window(self, cell_config, parent):
        orientation = cell_config.get('paned_window_orientation','horizontal')
        paned_window = ttk.Panedwindow(parent, orient=orientation)
        return paned_window   

    def get_frame(self,root,cell_config: Dict) -> tk.Frame:
        """Get a frame positioned at the specified grid location."""
        frame = tk.Frame(
            root,
            bd=cell_config.get("bd", 0),
            highlightthickness=cell_config.get("highlightthickness", 0),
            bg=cell_config.get("bg", "black"),
        )  

        return frame
       
    def get_window_component_by_name(self, name: str) -> Optional["WindowComponent"]:
        """Return the WindowComponent with the given name, or None if not found."""
        for cell in self.window_components:
            if cell.name == name:
                return cell
        return None

    def refresh_grids(self):
        """Refresh all grids."""
        for cell in self.window_components:
            if cell.type == "media_tree":
                cell.treeview.refresh()
