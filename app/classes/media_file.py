from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os

@dataclass
class MediaFile:
    file_size_kb: int
    media_folder: "MediaFolder"
    file_id: str
    file_name: int

    # derived fields – no imports needed
    _file_extension: str = field(init=False, default="", repr=False)
    _media_type: str     = field(init=False, default="unknown", repr=False)

    def __post_init__(self) -> None:
        self._file_extension = os.path.splitext(self.file_name)[1].lower()
        self._media_folder = self.media_folder

    @property
    def file_extension(self) -> str:
        """Return the file‑extension (including the leading dot)."""
        return self._file_extension

    @property
    def media_type(self) -> str:
        """Return the current media type – can be overridden later."""
        return self._media_type

    @media_type.setter
    def media_type(self, value: str) -> None:
        self._media_type = value

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def to_tuple(self) -> tuple:
        """Return a tuple suitable for a DB INSERT."""
        return (
            self.file_id,
            self.media_folder.folder_id,
            self.file_name,
            self.file_size_kb,
        )

    def get_path(self) -> str:
        """Return the absolute path to the file."""
        return os.path.join(self.media_folder.folder_path, self.file_name)

    def get_id(self) -> int:
        return self.file_id