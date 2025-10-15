# /app/classes/content_frame.py
from .media_file import MediaFile
from .media_folder import MediaFolder
from .image_manager import ImageManager

class ContentFrame:
    """A class to manage the content frame, responding to a selection such as from the treeview."""
    
    def __init__(self, media_manager, grid_cell):
        self.grid_cell = grid_cell
        self.media_manager = media_manager
        #by default open an image manager as placeholder
        self.image_manager = ImageManager(self.grid_cell.frame)

    def display_media(self, media):
        """Display a MediaFile or MediaFolder in the content frame."""

        if isinstance(media, MediaFile):
            if media.media_type == 'image':
                if not self.image_manager:
                    self.image_manager = ImageManager(self.grid_cell.frame)
                self.image_manager.preload_image(media.get_path())
                self.image_manager.display_preloaded_image()
            else:
                print(f"Unsupported media type: {media.media_type}")
                self.set_placeholder()

        elif isinstance(media, MediaFolder):
            # Implement folder display logic here
            print(f"Displaying folder: {media.folder_path}")
            self.set_placeholder()
        else:
            self.set_placeholder()
            print("Unsupported media type or object")

    def preload_media_file(self, media):
        if isinstance(media, MediaFile):
            if media.media_type == 'image':
                self.image_manager.preload_image(media.get_path())   
    
    def show_preloaded_media(self, media):
        if isinstance(media, MediaFile):
            if media.media_type == 'image':
                self.image_manager.display_preloaded_image()  

    def set_placeholder(self):
        """Set a placeholder in the content frame."""
        if not self.image_manager:
            self.image_manager = ImageManager(self.grid_cell.frame)
        self.image_manager.clear()


    
        


