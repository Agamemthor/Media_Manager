from .media_file import MediaFile
from .image_manager import ImageManager

class ContentFrame:
    """A class to manage the content frame, responding to a selection such as from the treeview."""
    
    def __init__(self, media_manager, parent):
        self.frame = parent
        self.media_manager = media_manager
        #by default open an image manager as placeholder
        self.image_manager = ImageManager(self.frame)

    def display_media(self, media):
        """Display a MediaFile or MediaFolder in the content frame."""
        from .media_folder import MediaFolder  # Import here if needed

        if isinstance(media, MediaFile):
            if media.media_type == 'image':
                if not self.image_manager:
                    self.image_manager = ImageManager(self.frame)
                self.image_manager.display_image(media.file_path)
            else:
                print(f"Unsupported media type: {media.media_type}")
                self.set_placeholder()

        elif isinstance(media, MediaFolder):
            # Implement folder display logic here
            print(f"Displaying folder: {media.folder_path}")
            self.set_placeholder()
        else:
            print("Unsupported media type or object")
        
    def set_placeholder(self):
        """Set a placeholder in the content frame."""
        if not self.image_manager:
            self.image_manager = ImageManager(self.frame)
        self.image_manager.load_placeholder()


    
        


