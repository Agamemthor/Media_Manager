import tkinter as tk
from tkinter import ttk
import logging
from .media_file import MediaFile
from .media_folder import MediaFolder
from .image_manager import ImageManager

logger = logging.getLogger(__name__)

class ContentFrame:
    """Manages the content frame, responding to selections such as from the treeview."""

    def __init__(self, media_manager, window_component):
        self.window_component = window_component
        self.media_manager = media_manager
        self.image_manager = ImageManager(self.window_component.frame)

    def display_media(self, media):
        """Display a MediaFile or MediaFolder in the content frame."""
        if isinstance(media, MediaFile):
            if media.media_type == "image":
                self.image_manager.preload_image(media.get_path())
                self.image_manager.display_preloaded_image()
            else:
                logger.warning(f"Unsupported media type: {media.media_type}")
                self.set_placeholder()
        elif isinstance(media, MediaFolder):
            logger.info(f"Displaying folder: {media.folder_path}")
            self.set_placeholder()
        else:
            self.set_placeholder()
            logger.warning("Unsupported media type or object")

    def preload_media_file(self, media):
        """Preload a media file."""
        if isinstance(media, MediaFile) and media.media_type == "image":
            self.image_manager.preload_image(media.get_path())

    def show_preloaded_media(self, media):
        """Show preloaded media."""
        if isinstance(media, MediaFile) and media.media_type == "image":
            self.image_manager.display_preloaded_image()

    def set_placeholder(self):
        """Set a placeholder in the content frame."""
        self.image_manager.clear()
