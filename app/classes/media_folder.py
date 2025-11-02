from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class MediaFolder:
    folder_id: int
    folder_path: str
    parent_folder_id: Optional[int] = None

    # internal (read‑only) fields – no imports needed
    _parent: Optional["MediaFolder"] = field(init=False, default=None, repr=False)
    _files: List["MediaFile"] = field(init=False, default_factory=list, repr=False)
    _subfolders: List["MediaFolder"] = field(init=False, default_factory=list, repr=False)

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def to_tuple(self) -> tuple:
        """Return a tuple suitable for a DB INSERT."""
        return (self.folder_id, self.folder_path, self.parent_folder_id)

    @property
    def parent(self) -> Optional["MediaFolder"]:
        return self._parent

    @property
    def files(self) -> List["MediaFile"]:
        return self._files

    @property
    def subfolders(self) -> List["MediaFolder"]:
        return self._subfolders

    def get_files_recursive(self) -> List["MediaFile"]:
        """Return all files in this folder and its subfolders."""
        all_files = self._files.copy()
        for folder in self._subfolders:
            all_files.extend(folder.get_files_recursive())
        return all_files

    def get_folders_recursive(self) -> List["MediaFolder"]:
        """Return all subfolders recursively."""
        all_folders = self._subfolders.copy()
        for folder in self._subfolders:
            all_folders.extend(folder.get_folders_recursive())
        return all_folders

    def get_id(self) -> int:
        return self.folder_id