from tkinter import ttk, Menu
from typing import Dict, Optional, List, Any
import os
import platform
import subprocess
import logging
from .media_file import MediaFile
from .media_folder import MediaFolder
from .slideshow_manager import MultiSlideshow
from .content_frame import ContentFrame

logger = logging.getLogger(__name__)

class TreeviewManager:
    def __init__(self, window_component, media_manager, frame):
        self.window_component = window_component
        self.media_manager = media_manager
        self.frame = frame
        self.item_to_object: Dict[str, Any] = {}
        self.content_frame_cell: ContentFrame = None
        self._arrow_delay_active = False
        self.initialize_treeview()

    def initialize_treeview(self):
        """Initialize the treeview."""
        self.tree = ttk.Treeview(self.frame)
        self.tree.pack(side="left", fill="both", expand=True)
        self._configure_columns()
        self.bind_events()

    def _configure_columns(self):
        """Configure the treeview columns."""
        config = self.window_component.cell_config.get("treeview", {})
        self.tree["columns"] = config.get("columns", ["type", "size", "path"])

        for col_id, col_cfg in config.get("column_configs", {}).items():
            self.tree.column(
                col_id,
                width=col_cfg.get("width", 100),
                stretch=col_cfg.get("stretch", False),
                anchor=col_cfg.get("anchor", "w")
            )
            self.tree.heading(
                col_id,
                text=col_cfg.get("heading", col_id)
        )

    def bind_events(self):
        """Bind all necessary events for the treeview."""
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Button-1>", self._close_context_menu_on_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_treeview_select)

    def populate(self):
        """Populate the treeview using the MediaManager data."""
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.item_to_object = {}
            for folder in self.media_manager.get_root_folders():
                self._add_folder_to_treeview("", folder)
        except Exception as e:
            logger.exception("Failed to populate treeview")
            raise Exception(f"Failed to populate treeview: {e}")

    def _add_folder_to_treeview(self, parent_item_id: str, folder: MediaFolder) -> str:
        """Recursively add a folder and its contents to the treeview."""
        folder_item_id = self.tree.insert(
            parent_item_id,
            "end",
            text=os.path.basename(folder.folder_path),
            values=("", "", folder.folder_path),
            tags=("folder",),
        )
        self.item_to_object[folder_item_id] = folder
        for subfolder in folder.subfolders:
            self._add_folder_to_treeview(folder_item_id, subfolder)
        for file in folder.files:
            file_item_id = self.tree.insert(
                folder_item_id,
                "end",
                text=file.file_name,
                values=(
                    file.media_type,
                    f"{file.file_size_kb:,}",
                    file.folder_path,
                ),
                tags=("file",),
            )
            self.item_to_object[file_item_id] = file
        return folder_item_id

    def get_selected_object(self) -> Optional[Any]:
        """Get the MediaFolder or MediaFile object associated with the selected treeview item."""
        try:
            selected_items = self.tree.selection()
            if selected_items:
                return self.item_to_object.get(selected_items[0])
            return None
        except Exception as e:
            logger.error(f"Error getting selected object: {e}")
            return None

    def get_selected_objects(self) -> List[Any]:
        """Get all MediaFolder and MediaFile objects associated with selected treeview items."""
        selected_items = self.tree.selection()
        return [self.item_to_object.get(item) for item in selected_items if item in self.item_to_object]

    def clear(self):
        """Clear all items from the treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.item_to_object = {}

    def refresh(self):
        """Refresh the treeview with updated data from the MediaManager."""
        self.clear()
        self.populate()

    def set_content_frame_cell(self, content_frame_cell: ContentFrame):
        """Set the linked content frame cell to update on selection changes."""
        self.content_frame_cell = content_frame_cell

    def _on_treeview_select(self, event):
        """Handle treeview selection."""
        selected_item = self.tree.selection()
        if not selected_item:
            if self.content_frame_cell:
                self.content_frame_cell.display_media(None)
            else:
                logger.warning("No content_frame_cell set!")
            return
        selected_obj = self.get_selected_object()
        if selected_obj:
            if self.content_frame_cell and hasattr(self.content_frame_cell, "display_media"):
                self.content_frame_cell.display_media(selected_obj)
            else:
                logger.warning("No valid content_frame_cell set or missing display_media method!")

    def _show_context_menu(self, event):
        """Show the context menu at the clicked position."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree.focus(item)
            self.context_menu = Menu(self.tree, tearoff=0)
            selected_obj = self.item_to_object.get(item)
            self.context_menu.add_command(
                label="Show in Explorer",
                command=self._show_in_explorer,
            )
            if selected_obj and isinstance(selected_obj, MediaFolder):
                self.context_menu.add_command(
                    label="Start Slideshow",
                    command=lambda: self._start_folder_slideshow(selected_obj),
                )
            if selected_obj and isinstance(selected_obj, MediaFolder):
                self.context_menu.add_command(
                    label="Delete media folder",
                    command=lambda: self.media_manager.delete_media_folder(selected_obj),
                )
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
                self._current_menu = self.context_menu
            except Exception as e:
                logger.error(f"Error showing context menu: {e}")

    def _start_folder_slideshow(self, folder: MediaFolder):
        """Start a slideshow for all images in the selected folder."""
        folders = folder.get_folders_recursive()
        files = folder.get_files_recursive()
        self.media_manager.start_2x4_slideshow_in_new_window(folders, files)

    def _close_context_menu_on_click(self, event):
        """Close context menu when clicking, but only if it's open."""
        if hasattr(self, "_current_menu") and self._current_menu:
            try:
                self._current_menu.unpost()
                self._current_menu = None
            except Exception as e:
                logger.error(f"Error closing context menu: {e}")

    def _show_in_explorer(self):
        """Open the selected file or folder in the system's file explorer."""
        selected_item = self.tree.selection()
        if not selected_item:
            return
        item_id = selected_item[0]
        obj = self.item_to_object.get(item_id)
        if obj is None:
            return
        path = ""
        if isinstance(obj, MediaFolder):
            path = obj.folder_path
        elif isinstance(obj, MediaFile):
            path = os.path.join(obj.folder_path, obj.file_name)
        if not path or not os.path.exists(path):
            return
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", os.path.dirname(path)])

    def get_object_by_item(self, item_id: str) -> Optional[Any]:
        """Get the media object associated with a specific treeview item."""
        return self.item_to_object.get(item_id)

    def expand_all(self):
        """Expand all items in the treeview."""
        def expand(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                expand(child)
        for item in self.tree.get_children():
            expand(item)

    def collapse_all(self):
        """Collapse all items in the treeview."""
        def collapse(item):
            self.tree.item(item, open=False)
            for child in self.tree.get_children(item):
                collapse(child)
        for item in self.tree.get_children():
            collapse(item)
