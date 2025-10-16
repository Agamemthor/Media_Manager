from dataclasses import dataclass, field
import os

@dataclass
class MediaFile:
    folder_id: int
    file_name: str
    file_extension: str
    file_size_kb: int
    folder_path: str
    _media_type: str = field(init=False, default="unknown", repr=False)

    @property
    def media_type(self) -> str:
        """Get the media type based on file extension."""
        return self._media_type

    @media_type.setter
    def media_type(self, value: str):
        """Set the media type."""
        self._media_type = value

    def to_tuple(self) -> tuple:
        """Convert to tuple for database insertion."""
        return (
            self.folder_id,
            self.file_name,
            self.file_extension,
            self.file_size_kb,
            self.folder_path,
        )

    def get_path(self) -> str:
        """Get the full file path."""
        return os.path.join(self.folder_path, f"{self.file_name}")
