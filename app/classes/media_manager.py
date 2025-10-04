# /app/classes/media_manager.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from .media_folder import MediaFolder
from .media_file import MediaFile

@dataclass
class MediaManager:
    def __init__(self, folders: List[MediaFolder], files: List[MediaFile], extension_to_type: Dict[str, str]):
        """
        Initialize the MediaManager with lists of folders and files.
        Processes the data to establish relationships between objects.
        """
        self.folders: List[MediaFolder] = folders
        self.files: List[MediaFile] = files
        self.extension_to_type = extension_to_type

        # Create lookup dictionaries for faster access
        self.folder_by_id: Dict[int, MediaFolder] = {f.folder_id: f for f in folders}
        self.folder_by_path: Dict[str, MediaFolder] = {f.folder_path: f for f in folders}

        # Set media types for all files
        self._set_media_types()

        # Establish folder relationships
        self._build_folder_hierarchy()

        # Assign files to their folders
        self._assign_files_to_folders()

    def _set_media_types(self):
        """Set media types for all files based on their extensions"""
        for file in self.files:
            file.media_type = self.extension_to_type.get(file.file_extension.lower(), "unknown")

    def _build_folder_hierarchy(self):
        """Build the folder hierarchy by setting parent references"""
        for folder in self.folders:
            if folder.parent_folder_id:
                parent = self.folder_by_id.get(folder.parent_folder_id)
                if parent:
                    folder._parent = parent
                    parent._subfolders.append(folder)

    def _assign_files_to_folders(self):
        """Assign files to their respective folders"""
        for file in self.files:
            folder = self.folder_by_id.get(file.folder_id)
            if folder:
                folder._files.append(file)

    def get_folder_by_id(self, folder_id: int) -> Optional[MediaFolder]:
        """Get a folder by its ID"""
        return self.folder_by_id.get(folder_id)

    def get_folder_by_path(self, folder_path: str) -> Optional[MediaFolder]:
        """Get a folder by its path"""
        return self.folder_by_path.get(folder_path)

    def get_root_folders(self) -> List[MediaFolder]:
        """Get all root folders (those with no parent)"""
        return [f for f in self.folders if f.parent_folder_id is None]

    def get_all_files(self) -> List[MediaFile]:
        """Get all files"""
        return self.files

    def get_files_by_extension(self, extension: str) -> List[MediaFile]:
        """Get all files with a specific extension"""
        return [f for f in self.files if f.file_extension.lower() == extension.lower()]

    def get_files_by_type(self, media_type: str) -> List[MediaFile]:
        """Get all files of a specific media type"""
        return [f for f in self.files if f.media_type.lower() == media_type.lower()]
