# /app/classes/host_manager.py
import os
from tkinter import messagebox, filedialog

class HostManager:
    def __init__(self,set_status):
        self.set_status = set_status
        
    def scan_media(self, folder_path, valid_extensions, min_file_id, min_folder_id):
        """
        Scan media files in a single pass, building folder hierarchy and collecting files.
        Returns a tuple of (folders_data, files_data) with complete hierarchy information.
        """
        try:
            folders_data = []  # List of MediaFolder tuples
            files_data = []    # List of MediaFile tuples

            # Assign unique IDs to folders as we encounter them
            folder_id_counter = min_folder_id + 1
            folder_id_map = {}  # {folder_path: folder_id}

            processed_files = min_file_id + 1
            file_count = 0  # Count of media files found

            # Single pass through all files and folders
            for root, dirs, files in os.walk(folder_path):
                # Process current folder
                if root not in folder_id_map:
                    # Assign ID to current folder
                    folder_id_map[root] = folder_id_counter
                    folder_id_counter += 1

                    # Determine parent folder ID
                    parent_id = None
                    parent_path = os.path.dirname(root)

                    # If parent exists in our map, use its ID
                    if parent_path in folder_id_map:
                        parent_id = folder_id_map[parent_path]

                    # Add to folders_datamin_id
                    folders_data.append((folder_id_map[root], root, parent_id))

                # Process files in current folder
                for file in files:
                    processed_files += 1
                    if processed_files % 100 == 0:  # Update progress every 100 files                        
                        self.set_status(f"Scanning {processed_files} files, found {file_count} media files...")

                    ext = os.path.splitext(file)[1].lower()
                    if ext in valid_extensions:
                        file_count += 1
                        full_path = os.path.join(root, file)
                        size = os.path.getsize(full_path) // 1024  # Size in KB

                        files_data.append((
                            folder_id_map[root],
                            file,
                            ext,
                            size,
                            root  # folder_path
                        ))

            self.set_status(f"Scanned {processed_files} files, found {file_count} media files.")
            return folders_data, files_data

        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan media: {e}")
            self.set_status("Error scanning media.")
            raise