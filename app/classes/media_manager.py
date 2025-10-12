# /app/classes/media_manager.py
from dataclasses import dataclass, field
from tkinter import messagebox, filedialog
from typing import List, Dict, Optional, Set
from .media_folder import MediaFolder
from .media_file import MediaFile
from .grid_manager import GridManager
from .window_manager import WindowManager
from .host_manager import HostManager   
from .db_manager import DBManager
from tkinter import ttk
import tkinter as tk

@dataclass
class MediaManager:
    """
    Represents a window, and coordinates all processes on that window.
    conn_config = {
        'dbname': 'media_manager',
        'user': 'youruser',
        'password': 'yourpassword',
        'host': 'localhost',
        'port': "5432",
        'retries': 5,
        'delay': 3
    }
    window_config = {
        'height': 600,
        'width': 800,
        'borderless': False, #the overrideredirect parameter is a fickle beast. Ignores the always_on_top parameter and app is always on top of everything
        'show_custom_titlebar': False,
        'title': "Media Manager",
        'show_menubar': False,
        'fullscreen': True, # does not work when borderless is True
        'always_on_top': False, # if borderless = true, app is always on top
        'exit_on_escape': True,  # does not work if borderless is True
        'fullscreen_on_f11': True,  # does not work if borderless is True
    }    
    grid_config = {
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
    """

    def __init__(self, db_config, window_config, grid_config):
        self.gridmanager = None
        self.host_manager = HostManager(set_status=self.set_status)
        self.window_manager = WindowManager(window_config)
        
        root=self.window_manager.get_root()
        self.root=root

        self.media_files: List[MediaFile] = []
        self.media_folders: List[MediaFolder] = []
        self.media_folder_by_id: Dict[int, MediaFolder] 
        self.media_folder_by_path: Dict[str, MediaFolder]

        self.grid_manager = GridManager(self, root, grid_config)  
        self.grid_manager.set_status("Loading data...")

        self.db_manager =  DBManager(db_config, set_status=self.set_status)   

        self.load_data() 
        
        self.grid_manager.set_status("Creating grid...")
        self.grid_manager.create_content()
        self.grid_manager.set_status("Ready.")

    def load_data(self):
        """
        Load media data from the database or scan for new data if none exists.
        """
        self.set_status("Loading from database...")

        self.extension_to_type, self.valid_extensions = self.db_manager.load_media_type_mappings()
        folders_data = self.db_manager.get_folders_from_db()
        files_data = self.db_manager.get_files_from_db()  

        if len(files_data) == 0:
            # No files found, ask user if they want to scan
            if messagebox.askyesno("Scan Media", "No media data found. Scan now?"):                
                self.set_status("Scanning for media files...")
                folders_data, files_data = self.get_media_from_folder()
            else:
                self.set_status("Ready.")
                return None

        self._add_files_and_folders(folders_data, files_data)

        self.set_status("Ready.")
    
    def get_media_from_folder(self):
        # Scan for media files
        max_file_id = max((f.folder_id for f in self.media_files), default=0)
        max_folder_id = max((f.folder_id for f in self.media_folders), default=0)

        folder_path = filedialog.askdirectory(title="Select root folder")
        if not folder_path:
            return None
        folders_data, files_data = self.host_manager.scan_media(valid_extensions=self.valid_extensions,folder_path=folder_path, min_file_id=max_file_id, min_folder_id=max_folder_id)

        self.set_status("Saving to database...")
        # Save to database
        self.db_manager.save_to_db(folders_data, files_data)

        return folders_data, files_data        

    def _add_files_and_folders(self, folders_data, files_data):
        # Create MediaFolder and MediaFile objects from raw data
        folders = []
        for row in folders_data:
            folder = MediaFolder(
                folder_id=row[0],
                folder_path=row[1],
                parent_folder_id=row[2]
            )
            folders.append(folder)
        self.media_folders.extend(folders)

        files = []
        for row in files_data:
            file = MediaFile(
                folder_id=row[0],
                file_name=row[1],
                file_extension=row[2],
                file_size_kb=row[3],
                folder_path=row[4]
            )
            file._media_type = self.extension_to_type.get(file.file_extension.lower(), "unknown")
            files.append(file)
        self.media_files.extend(files)

        self.update_media_data()

    def update_media_data(self):
        self.media_folder_by_id: Dict[int, MediaFolder] = {f.folder_id: f for f in self.media_folders}
        self.media_folder_by_path: Dict[str, MediaFolder] = {f.folder_path: f for f in self.media_folders}

        """Build the folder hierarchy by setting parent references"""
        for folder in self.media_folders:
            if folder.parent_folder_id:
                parent = self.media_folder_by_id.get(folder.parent_folder_id)
                if parent:
                    folder._parent = parent
                    parent._subfolders.append(folder)

        """Assign files to their respective folders
        clean up existing assignments first"""
        for folder in self.media_folders:
            folder._files = []  # Initialize empty list

        for file in self.media_files:
            folder = self.media_folder_by_id.get(file.folder_id)
            if folder:
                folder._files.append(file)

    def set_status(self, status_text: str):
        if self.gridmanager:
            self.gridmanager.set_status(status_text) 

    def get_folder_by_id(self, folder_id: int) -> Optional[MediaFolder]:
        """Get a folder by its ID"""
        return self.folder_by_id.get(folder_id)

    def get_folder_by_path(self, folder_path: str) -> Optional[MediaFolder]:
        """Get a folder by its path"""
        return self.folder_by_path.get(folder_path)

    def get_root_folders(self) -> List[MediaFolder]:
        """Get all root folders (those with no parent)"""
        return [f for f in self.media_folders if f.parent_folder_id is None]

    def get_all_files(self) -> List[MediaFile]:
        """Get all files"""
        return self.media_files

    def get_files_by_extension(self, extension: str) -> List[MediaFile]:
        """Get all files with a specific extension"""
        return [f for f in self.media_files if f.file_extension.lower() == extension.lower()]

    def get_files_by_type(self, media_type: str) -> List[MediaFile]:
        """Get all files of a specific media type"""
        return [f for f in self.media_files if f.media_type.lower() == media_type.lower()]
    
    def delete_media_folder(self, folder: MediaFolder):
        """
        Delete a media folder and all its subfolders and files from the database and internal structures.
        """
        if not messagebox.askyesno("Delete Media Folder", f"Are you sure you want to delete the folder '{folder.folder_path}' and all its contents? This action cannot be undone."):
            return

        try:
            folder_ids_to_delete = set()
            folder_ids_to_delete.add(folder.folder_id)
            subfolders = folder.get_folders_recursive()
            for folder in subfolders:
                folder_ids_to_delete.add(folder.folder_id)
            
            # Delete from database
            self.db_manager.delete_folders_and_files(folder_ids_to_delete)

            # Remove from internal structures
            _media_folders = [f for f in self.media_folders if f.folder_id not in folder_ids_to_delete]
            _media_files = [f for f in self.media_files if f.folder_id not in folder_ids_to_delete]
            self.media_folders = _media_folders
            self.media_files = _media_files
            self.update_media_data()

            # Refresh the UI
            if self.grid_manager:
                self.grid_manager.refresh_grids()

            self.db_manager.commit()            
            self.set_status(f"Deleted folder '{folder.folder_path}'.")
        except Exception as e:
            self.db_manager.rollback()
            messagebox.showerror("Error", f"An error occurred while deleting the folder: {e}")
            self.set_status("Error occurred during deletion.")

            
