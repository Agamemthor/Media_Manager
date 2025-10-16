import os
from tkinter import messagebox, filedialog
import logging
from typing import List, Tuple, Set

logger = logging.getLogger(__name__)

class HostManager:
    def __init__(self, set_status):
        self.set_status = set_status

    def scan_media(
        self,
        folder_path: str,
        valid_extensions: Set[str],
        min_file_id: int,
        min_folder_id: int,
    ) -> Tuple[List[Tuple], List[Tuple]]:
        """Scan media files in a single pass, building folder hierarchy and collecting files."""
        try:
            folders_data = []
            files_data = []
            folder_id_counter = min_folder_id + 1
            folder_id_map = {}
            processed_files = min_file_id + 1
            file_count = 0

            for root, dirs, files in os.walk(folder_path):
                if root not in folder_id_map:
                    folder_id_map[root] = folder_id_counter
                    folder_id_counter += 1
                    parent_id = None
                    parent_path = os.path.dirname(root)
                    if parent_path in folder_id_map:
                        parent_id = folder_id_map[parent_path]
                    folders_data.append((folder_id_map[root], root, parent_id))

                for file in files:
                    processed_files += 1
                    if processed_files % 100 == 0:
                        self.set_status(f"Scanning {processed_files} files, found {file_count} media files...")
                    ext = os.path.splitext(file)[1].lower()
                    if ext in valid_extensions:
                        file_count += 1
                        full_path = os.path.join(root, file)
                        size = os.path.getsize(full_path) // 1024
                        files_data.append(
                            (
                                folder_id_map[root],
                                file,
                                ext,
                                size,
                                root,
                            )
                        )

            self.set_status(f"Scanned {processed_files} files, found {file_count} media files.")
            return folders_data, files_data
        except Exception as e:
            logger.exception("Failed to scan media")
            messagebox.showerror("Error", f"Failed to scan media: {e}")
            self.set_status("Error scanning media.")
            raise
