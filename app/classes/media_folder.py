# /app/classes/media_folder.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from .media_file import MediaFile  # Import MediaFile for type hints

@dataclass
class MediaFolder:
    folder_id: int
    folder_path: str
    parent_folder_id: Optional[int] = None
    _parent: Optional['MediaFolder'] = field(init=False, default=None, repr=False)
    _files: List[MediaFile] = field(init=False, default_factory=list, repr=False)
    _subfolders: List['MediaFolder'] = field(init=False, default_factory=list, repr=False)

    def to_tuple(self):
        """Convert to tuple for database insertion"""
        return (self.folder_id, self.folder_path, self.parent_folder_id)

    @property
    def parent(self) -> Optional['MediaFolder']:
        """Get the parent folder"""
        return self._parent

    @property
    def files(self) -> List[MediaFile]:
        """Get files in this folder (non-recursive)"""
        return self._files

    @property
    def subfolders(self) -> List['MediaFolder']:
        """Get subfolders of this folder (non-recursive)"""
        return self._subfolders

    def get_files_recursive(self) -> List[MediaFile]:
        """Get all files in this folder and its subfolders (recursive)"""
        all_files = self._files.copy()
        for folder in self._subfolders:
            all_files.extend(folder.get_files_recursive())
        return all_files
    