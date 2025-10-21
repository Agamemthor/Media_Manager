import json
from dataclasses import dataclass, field
from tkinter import messagebox, filedialog
from typing import List, Dict, Optional, Set, Tuple
import logging
from .media_folder import MediaFolder
from .media_file import MediaFile
from .window_component_manager import WindowComponentManager
from .window_manager import WindowManager
from .host_manager import HostManager
from .db_manager import DBManager
from .content_frame import ContentFrame
from .slideshow_manager import MultiSlideshow

logger = logging.getLogger(__name__)

@dataclass
class MediaManager:
    """Coordinates all processes on the window."""

    def __init__(
        self,
        conn_config: Dict,
        window_config: Dict,
        grid_config: Dict,
        window_manager_config: Dict = None,
        media_folders: List[MediaFolder] = None,
        media_files: List[MediaFile] = None,
        parent_manager: Optional["MediaManager"] = None,
    ):
        self.WindowComponentManager = None
        self.parent_manager = parent_manager
        self.sub_media_managers: List["MediaManager"] = []
        self.host_manager = HostManager(set_status=self.set_status)
        self.window_manager = WindowManager(parent_manager, window_config, window_manager_config)
        self.slideshow_config = grid_config.get("slideshow", {})
        self.slideshow_manager = MultiSlideshow(self)
        self.db_manager = DBManager(conn_config, set_status=self.set_status)

        root = self.window_manager.get_root()
        self.root = root
        self.grid_manager = WindowComponentManager(self, root, grid_config)
        self.media_folder_by_id: Dict[int, MediaFolder]
        self.media_folder_by_path: Dict[str, MediaFolder]

        if media_files and media_folders:
            self.media_files = media_files
            self.media_folders = media_folders
            self.update_media_data()
            if len(self.slideshow_manager.slideshow_cells) > 0:
                self.slideshow_manager._start_slideshows(self.media_files)
        else:
            self.media_files: List[MediaFile] = []
            self.media_folders: List[MediaFolder] = []

            self.grid_manager.set_status("Loading data...")
            self.load_data()

            self.grid_manager.set_status("Creating grid...")
            self.grid_manager.create_content()
            self.grid_manager.set_status("Ready.")

    def load_data(self):
        """Load media data from the database or scan for new data if none exists."""
        self.set_status("Loading from database...")
        self.extension_to_type, self.valid_extensions = self.db_manager.load_media_type_mappings()
        folders_data = self.db_manager.get_folders_from_db()
        files_data = self.db_manager.get_files_from_db()
        if len(files_data) == 0:
            if messagebox.askyesno("Scan Media", "No media data found. Scan now?"):
                self.set_status("Scanning for media files...")
                folders_data, files_data = self.get_media_from_folder()
            else:
                self.set_status("Ready.")
                return None
        self._add_files_and_folders(folders_data, files_data)
        self.set_status("Ready.")

    def get_media_from_folder(self):
        """Scan for media files."""
        max_file_id = max((f.folder_id for f in self.media_files), default=0)
        max_folder_id = max((f.folder_id for f in self.media_folders), default=0)
        folder_path = filedialog.askdirectory(title="Select root folder")
        if not folder_path:
            return None
        folders_data, files_data = self.host_manager.scan_media(
            valid_extensions=self.valid_extensions,
            folder_path=folder_path,
            min_file_id=max_file_id,
            min_folder_id=max_folder_id,
        )
        self.set_status("Saving to database...")
        self.db_manager.save_to_db(folders_data, files_data)
        return folders_data, files_data

    def _add_files_and_folders(self, folders_data: List[Tuple], files_data: List[Tuple]):
        """Create MediaFolder and MediaFile objects from raw data."""
        folders = []
        for row in folders_data:
            folder = MediaFolder(
                folder_id=row[0],
                folder_path=row[1],
                parent_folder_id=row[2],
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
                folder_path=row[4],
            )
            file._media_type = self.extension_to_type.get(file.file_extension.lower(), "unknown")
            files.append(file)
        self.media_files.extend(files)
        self.update_media_data()

    def set_status(self, status_text: str):
        """Set the status text."""
        if self.WindowComponentManager:
            self.WindowComponentManager.set_status(status_text)

    def get_folder_by_id(self, folder_id: int) -> Optional[MediaFolder]:
        """Get a folder by its ID."""
        return self.folder_by_id.get(folder_id)

    def get_folder_by_path(self, folder_path: str) -> Optional[MediaFolder]:
        """Get a folder by its path."""
        return self.folder_by_path.get(folder_path)

    def get_root_folders(self) -> List[MediaFolder]:
        """Get all root folders (those with no parent)."""
        return [f for f in self.media_folders if f.parent_folder_id is None]

    def get_all_files(self) -> List[MediaFile]:
        """Get all files."""
        return self.media_files

    def get_files_by_extension(self, extension: str) -> List[MediaFile]:
        """Get all files with a specific extension."""
        return [f for f in self.media_files if f.file_extension.lower() == extension.lower()]

    def get_files_by_type(self, media_type: str) -> List[MediaFile]:
        """Get all files of a specific media type."""
        return [f for f in self.media_files if f.media_type.lower() == media_type.lower()]

    def update_media_data(self):
        """Update media data."""
        for folder in self.media_folders:
            folder._parent = None
            folder._files = []
            folder._subfolders = []
        self.media_folder_by_id: Dict[int, MediaFolder] = {f.folder_id: f for f in self.media_folders}
        self.media_folder_by_path: Dict[str, MediaFolder] = {f.folder_path: f for f in self.media_folders}
        for folder in self.media_folders:
            if folder.parent_folder_id:
                parent = self.media_folder_by_id.get(folder.parent_folder_id)
                if parent:
                    folder._parent = parent
                    parent._subfolders.append(folder)
        for file in self.media_files:
            folder = self.media_folder_by_id.get(file.folder_id)
            if folder:
                folder._files.append(file)

    def delete_media_folder(self, folder: MediaFolder):
        """Delete a media folder and all its subfolders and files from the database and internal structures."""
        if not messagebox.askyesno(
            "Delete Media Folder",
            f"Are you sure you want to delete the folder '{folder.folder_path}' and all its contents? This action cannot be undone.",
        ):
            return
        try:
            folder_ids_to_delete = set()
            folder_ids_to_delete.add(folder.folder_id)
            subfolders = folder.get_folders_recursive()
            for folder in subfolders:
                folder_ids_to_delete.add(folder.folder_id)

            self.db_manager.delete_folders_and_files(folder_ids_to_delete)
            self.media_folders = [f for f in self.media_folders if f.folder_id not in folder_ids_to_delete]
            self.media_files = [f for f in self.media_files if f.folder_id not in folder_ids_to_delete]
            self.update_media_data()
            if self.grid_manager:
                self.grid_manager.refresh_grids()
            self.db_manager.commit()
            self.set_status(f"Deleted folder '{folder.folder_path}'.")
        except Exception as e:
            self.db_manager.rollback()
            logger.exception("Failed to delete media folder")
            messagebox.showerror("Error", f"An error occurred while deleting the folder: {e}")
            self.set_status("Error occurred during deletion.")

    def start_2x4_slideshow_in_new_window(
        self, media_folders: List[MediaFolder], media_files: List[MediaFile]
    ):
        """Start a new MediaManager instance with slideshow configuration for the given media files."""
        # Load slideshow-specific configuration
        with open("configs/slideshow_2x4.json", "r") as f:
            slideshow_config = json.load(f)

        window_config = slideshow_config["window"]

        grid_config = slideshow_config["custom_grid"]

        self.start_new_media_manager(
            window_config,
            grid_config,
            media_folders=media_folders,
            media_files=media_files,
        )

    def start_new_media_manager(
        self,
        window_config: Dict,
        grid_config: Dict,
        media_folders: List[MediaFolder] = None,
        media_files: List[MediaFile] = None,
    ):
        """Start a new MediaManager instance."""
        media_manager = MediaManager(
            conn_config=self.db_manager.conn_config,
            window_config=window_config,
            grid_config=grid_config,
            parent_manager=self,
            media_folders=media_folders,
            media_files=media_files,
        )
        self.sub_media_managers.append(media_manager)

