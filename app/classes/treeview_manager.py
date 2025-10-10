# /app/classes/treeview_manager.py
#import tkinter as tk
from tkinter import ttk, Menu
from typing import Dict, Optional, List, Any
import os
import platform
import subprocess
from .media_file import MediaFile 
from .media_folder import MediaFolder 
from .slideshow_manager import MultiSlideshowWindow 

class TreeviewManager:
    def __init__(self, media_manager, frame):

        self.media_manager = media_manager   
        self.frame = frame
        self.item_to_object: Dict[str, Any] = {}  # Maps item IDs to MediaFolder/MediaFile objects
        
        self.initialize_treeview()              

    def initialize_treeview(self):
        self.tree = ttk.Treeview(self.frame)
        self.tree.pack(side="left", fill="both", expand=True)

        self._configure_columns()
        self.bind_events()

    def _configure_columns(self):
        """Configure the treeview columns"""
        self.tree["columns"] = ("type", "size", "path")
        self.tree.column("#0", width=300, stretch=True)  # Name column
        self.tree.column("type", width=100, anchor="w")
        self.tree.column("size", width=80, anchor="e")
        self.tree.column("path", width=200, stretch=True)

        # Set column headings
        self.tree.heading("#0", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("size", text="Size (KB)")
        self.tree.heading("path", text="Path")


    def bind_events(self):
        """Bind all necessary events for the treeview"""
        # Bind right-click for context menu
        self.tree.bind("<Button-3>", self._show_context_menu)

        # Bind left click to close context menu
        self.tree.bind("<Button-1>", self._close_context_menu_on_click)

        # Bind focus out to close context menu
        self.tree.bind("<FocusOut>", self._close_context_menu_on_click)

        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_treeview_select)

    def populate(self, media_manager):
        """
        Populate the treeview using the MediaManager data.

        Args:
            media_manager: The MediaManager instance containing the media data
        """
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Clear the item-to-object mapping
            self.item_to_object = {}

            # Add root folders
            for folder in media_manager.get_root_folders():
                self._add_folder_to_treeview("", folder)  # Empty string for root items

        except Exception as e:
            raise Exception(f"Failed to populate treeview: {e}")

    def _add_folder_to_treeview(self, parent_item_id, folder):
        """
        Recursively add a folder and its contents to the treeview.
        Subfolders are inserted first, followed by files.

        Args:
            parent_item_id: The parent item ID (empty string for root items)
            folder: The MediaFolder object to add

        Returns:
            The created treeview item ID
        """
        # Create folder item
        folder_item_id = self.tree.insert(
            parent_item_id,
            "end",
            text=os.path.basename(folder.folder_path),
            values=("", "", folder.folder_path),  # Empty values for type and size
            tags=("folder",)
        )

        # Store the association between item and folder
        self.item_to_object[folder_item_id] = folder

        # First add subfolders
        for subfolder in folder.subfolders:
            self._add_folder_to_treeview(folder_item_id, subfolder)

        # Then add files in this folder
        for file in folder.files:
            file_item_id = self.tree.insert(
                folder_item_id,
                "end",
                text=file.file_name,
                values=(
                    file.media_type,
                    f"{file.file_size_kb:,}",
                    file.folder_path
                ),
                tags=("file",)
            )
            self.item_to_object[file_item_id] = file

        return folder_item_id

    def get_selected_object(self):
        """
        Get the MediaFolder or MediaFile object associated with the selected treeview item.
        Returns None if no item is selected.
        """
        try:
            selected_items = self.tree.selection()
            if selected_items:
                return self.item_to_object.get(selected_items[0])
            return None
        except Exception as e:
            print(f"Error getting selected object: {e}")
            return None

    def get_selected_objects(self):
        """
        Get all MediaFolder and MediaFile objects associated with selected treeview items.

        Returns:
            A list of media objects (can be empty if no items are selected)
        """
        selected_items = self.tree.selection()
        return [self.item_to_object.get(item) for item in selected_items if item in self.item_to_object]

    def clear(self):
        """Clear all items from the treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.item_to_object = {}

    def refresh(self, media_manager):
        """Refresh the treeview with updated data from the MediaManager"""
        self.clear()
        self.populate(media_manager)

    def _on_treeview_select(self, event):
        """Handle treeview selection changes to update the image display"""
        selected_item = self.tree.selection()
        if not selected_item:
            if self.media_manager:
                self.media_manager.clear_content_frame()
            return

        # Get the selected object
        selected_obj = self.get_selected_object()

        if selected_obj and isinstance(selected_obj, MediaFile):
            # Check if it's an image file
            if selected_obj.media_type.lower() in ["image", "gif"]:
                # Construct the full path
                full_path = os.path.join(selected_obj.folder_path, selected_obj.file_name)

                # Display the image if we have an ImageManager
                if self.image_manager:
                    self.image_manager.display_image(full_path)
            else:
                # Clear if not an image
                if self.image_manager:
                    self.image_manager.clear()
        else:
            # Clear if not a file
            if self.image_manager:
                self.image_manager.clear()


    # In your TreeviewManager class
    def _show_context_menu(self, event):
        """Show the context menu at the clicked position"""
        # Close any existing menu
        #self._close_context_menu_on_click()

        # Select the item under the cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree.focus(item)

            # Create context menu
            self.context_menu = Menu(self.tree, tearoff=0)

            # Get the selected object
            selected_obj = self.item_to_object.get(item)

            # Add "Show in Explorer" option (always available)
            self.context_menu.add_command(
                label="Show in Explorer",
                command=self._show_in_explorer
            )

            # Add "Start Slideshow" option only for folders
            if selected_obj and isinstance(selected_obj, MediaFolder):
                self.context_menu.add_command(
                    label="Start Slideshow",
                    command=lambda: self._start_folder_slideshow(selected_obj)
                )

            # Show the menu
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
                # Store the menu reference for later cleanup
                self._current_menu = self.context_menu
            except Exception as e:
                print(f"Error showing context menu: {e}")

    def _start_folder_slideshow(self, folder: MediaFolder):
        """Start a slideshow for all images in the selected folder."""
        # Get all image files recursively from the folder
        all_files = folder.get_files_recursive()
        self.multi_slideshow_manager = MultiSlideshowWindow(all_files)
        # Create and start the multi-slideshow
        self.multi_slideshow_manager.start_slideshows(all_files)

    def _close_context_menu_on_click(self, event):
        """Close context menu when clicking, but only if it's open"""
        if hasattr(self, '_current_menu') and self._current_menu:
            try:
                self._current_menu.unpost()
                self._current_menu = None
            except Exception as e:
                print(f"Error closing context menu: {e}")

    def _show_in_explorer(self):
        """Open the selected file or folder in the system's file explorer"""
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

        # Open in system file explorer
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", path])
        else:  # Linux and other Unix-like systems
            subprocess.run(["xdg-open", os.path.dirname(path)])

    def get_object_by_item(self, item_id):
        """
        Get the media object associated with a specific treeview item.

        Args:
            item_id: The treeview item ID

        Returns:
            The associated media object, or None if not found
        """
        return self.item_to_object.get(item_id)

    def expand_all(self):
        """Expand all items in the treeview"""
        def expand(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                expand(child)

        for item in self.tree.get_children():
            expand(item)

    def collapse_all(self):
        """Collapse all items in the treeview"""
        def collapse(item):
            self.tree.item(item, open=False)
            for child in self.tree.get_children(item):
                collapse(child)

        for item in self.tree.get_children():
            collapse(item)
