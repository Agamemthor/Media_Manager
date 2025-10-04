import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import psycopg2
from psycopg2 import OperationalError
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor
import platform
import subprocess
from PIL import Image
import cv2
from dataclasses import dataclass, field 
from typing import Dict, List, Tuple, Optional
from classes import MediaFile, MediaFolder, MediaManager, TreeviewManager, GridManager, ImageManager, MultiSlideshowWindow

def connect_to_db(retries=5, delay=3):
    for i in range(retries):
        try:
            conn = psycopg2.connect(
                dbname="media_manager",
                user="youruser",
                password="yourpassword",
                host="localhost",
                port="5432"
            )
            print("Connected to PostgreSQL!")
            return conn
        except OperationalError as e:
            print(f"Connection attempt {i + 1} failed: {e}")
            if i < retries - 1:
                time.sleep(delay)
    raise Exception("Could not connect to PostgreSQL after several retries.")

class MediaManagerApp:
    def __init__(self, root, conn):
        self.root = root
        self.conn = conn
        self.rootfolder = self.get_rootfolder()
        self.root.title(self.rootfolder)

        # Initialize GridManager with 2x2 grid (1 row for content, 1 row for status bar)
        grid_config = {
            'rows': 2,  # 2 rows: 1 for content, 1 for status bar
            'columns': 2,
            'row_weights': [1, 0],  # First row expands, second row fixed height
            'column_weights': [1, 3]  # Equal column weights
        }
        self.grid_manager = GridManager(root, grid_config)

        # Get frame for the treeview (left side, first row)
        self.treeview_frame = self.grid_manager.get_frame(row=0, column=0)

        # Get empty frame for the right side (first row)
        self.content_frame = self.grid_manager.get_frame(row=0, column=1)

        # Create an image frame inside the content frame
        self.image_frame = tk.Frame(self.content_frame)
        self.image_frame.pack(fill="both", expand=True)
        # Initialize ImageManager
        self.image_manager = ImageManager(self.image_frame)

        # Initialize MultiSlideshowWindow
        #

        # Initialize Treeview in the left frame
        self.tree = ttk.Treeview(self.treeview_frame)
        self.tree.pack(side="left", fill="both", expand=True)

        # Initialize TreeviewManager
        self.treeview_manager = TreeviewManager(self.tree, self.image_manager)
        #self.treeview_manager.multi_slideshow_manager = self.multi_slideshow_manager

        # Add a scrollbar to the treeview
        scrollbar = ttk.Scrollbar(self.treeview_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Create a menubar
        self.menubar = tk.Menu(root)
        self.root.config(menu=self.menubar)

        # Add a "File" menu
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="Select New Root Folder", command=self.change_rootfolder)
        self.menubar.add_cascade(label="File", menu=self.file_menu)

        # Create a status bar frame that spans both columns in the second row
        self.status_frame = self.grid_manager.get_frame(row=1, column=0, columnspan=2)

        # Add a status label to the status frame
        self.status = ttk.Label(self.status_frame, text="Ready", anchor="w", relief="sunken")
        self.status.pack(fill="x", padx=5, pady=2)

        # Load media type mappings
        self._load_media_type_mappings()

        # Load data
        self.load_data()

        # Populate treeview
        if self.media_manager:
            self.treeview_manager.populate(self.media_manager)

    def _load_media_type_mappings(self):
        """Load media type mappings from the database"""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT media_type_extension, media_type_description FROM media_types;")
            self.extension_to_type = {row[0].lower(): row[1] for row in cur.fetchall()}
            self.valid_extensions = set(self.extension_to_type.keys())
        except Exception as e:
            print(f"Error loading media type mappings: {e}")
            self.extension_to_type = {}
            self.valid_extensions = set()

    def get_rootfolder(self, force_new=False):
        cur = self.conn.cursor()
        if not force_new:
            # Only fetch the existing root folder if not forcing a new one
            cur.execute("SELECT Parameter_Value FROM Parameters WHERE Parameter_Name = 'rootfolder';")
            result = cur.fetchone()
            if result and result[0]:
                return result[0]

        # Prompt for a new root folder
        rootfolder = filedialog.askdirectory(title="Select Root Folder")
        if not rootfolder:
            self.root.destroy()
            return None

        # Save the new root folder to the database
        cur.execute(
            "INSERT INTO Parameters (Parameter_Name, Parameter_Value) "
            "VALUES ('rootfolder', %s) "
            "ON CONFLICT (Parameter_Name) DO UPDATE SET Parameter_Value = EXCLUDED.Parameter_Value;",
            (rootfolder,)
        )
        self.conn.commit()
        return rootfolder

    def change_rootfolder(self):
        # Warn the user about data loss
        if not messagebox.askyesno(
            "Warning",
            "This will DELETE all folder and file metadata. "
            "Are you sure you want to continue?"
        ):
            return  # User canceled
        try:
            # Delete all folder and file metadata
            cur = self.conn.cursor()
            cur.execute("DELETE FROM Media_Files;")
            cur.execute("DELETE FROM Media_Folders;")
            self.conn.commit()

            # Clear the treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Reuse get_rootfolder with force_new=True to prompt for a new folder
            self.rootfolder = self.get_rootfolder(force_new=True)
            self.root.title(self.rootfolder)

            # Scan the new root folder
            self.status["text"] = "Scanning new root folder..."
            self.root.update_idletasks()

            folders_data, files_data = self.scan_media(self.rootfolder)
            if len(folders_data) > 0:
                self.save_to_db(folders_data, files_data)

            # Create MediaFolder and MediaFile objects from scan results
            folders = []
            for row in folders_data:
                folder = MediaFolder(
                    folder_id=row[0],
                    folder_path=row[1],
                    parent_folder_id=row[2]
                )
                folders.append(folder)

            files = []
            for row in files_data:
                file = MediaFile(
                    folder_id=row[0],
                    file_name=row[1],
                    file_extension=row[2],
                    file_size_kb=row[3],
                    folder_path=row[4]
                )
                file._media_type = self.extension_to_type.get(file.file_extension.lower(), "unknown")
                files.append(file)

            # Create and return MediaManager
            self.media_manager = MediaManager(folders, files, self.extension_to_type)

            # Refresh the treeview
            self.status["text"] = "Populating treeview..."
            self.root.update_idletasks()
            self.treeview_manager.populate(self.media_manager)

            self.status["text"] = "Ready."
            self.root.update_idletasks()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to change root folder: {e}")
            self.status["text"] = "Error"

    def load_data(self):
        """
        Load media data from the database or scan for new data if none exists.
        Returns a MediaManager instance or None if loading failed.
        """
        try:
            cur = self.conn.cursor()

            # Check if we have any media files in the database
            cur.execute("SELECT COUNT(*) FROM media_files;")
            file_count = cur.fetchone()[0]

            if file_count == 0:
                # No files found, ask user if they want to scan
                if messagebox.askyesno("Scan Media", "No media data found. Scan now?"):
                    self.status["text"] = "Scanning for media files..."
                    self.root.update_idletasks()

                    # Scan for media files
                    folders_data, files_data = self.scan_media(self.rootfolder)

                    # Save to database
                    self.save_to_db(folders_data, files_data)

                    # Create MediaFolder and MediaFile objects from scan results
                    folders = []
                    for row in folders_data:
                        folder = MediaFolder(
                            folder_id=row[0],
                            folder_path=row[1],
                            parent_folder_id=row[2]
                        )
                        folders.append(folder)

                    files = []
                    for row in files_data:
                        file = MediaFile(
                            folder_id=row[0],
                            file_name=row[1],
                            file_extension=row[2],
                            file_size_kb=row[3],
                            folder_path=row[4]
                        )
                        file._media_type = self.extension_to_type.get(file.file_extension.lower(), "unknown")
                        files.append(file)

                    # Create and return MediaManager
                    self.media_manager = MediaManager(folders, files, self.extension_to_type)
                    self.status["text"] = "Media scan completed."
                    return self.media_manager
                else:
                    self.status["text"] = "No media data available."
                    return None
            else:
                # Load existing data from the database
                self.status["text"] = "Loading media data from database..."
                self.root.update_idletasks()

                # Load folders
                cur.execute("""
                    SELECT folder_id, folder_path, parent_folder_id
                    FROM media_folders
                    ORDER BY folder_path
                """)
                folders = []
                for row in cur.fetchall():
                    folder = MediaFolder(
                        folder_id=row[0],
                        folder_path=row[1],
                        parent_folder_id=row[2]
                    )
                    folders.append(folder)

                # Load files
                cur.execute("""
                    SELECT folder_id, file_name, file_extension, file_size_kb, folder_path
                    FROM media_files
                    ORDER BY folder_path, file_name
                """)
                files = []
                for row in cur.fetchall():
                    file = MediaFile(
                        folder_id=row[0],
                        file_name=row[1],
                        file_extension=row[2],
                        file_size_kb=row[3],
                        folder_path=row[4]
                    )
                    file._media_type = self.extension_to_type.get(file.file_extension.lower(), "unknown")
                    files.append(file)

                # Create and return MediaManager
                self.media_manager = MediaManager(folders, files, self.extension_to_type)
                self.status["text"] = f"Loaded {len(files)} media files."
                return self.media_manager

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load media data: {e}")
            self.status["text"] = "Error loading media data."
            return None

    def scan_media(self, folder_path):
        """
        Scan media files in a single pass, building folder hierarchy and collecting files.
        Returns a tuple of (folders_data, files_data) with complete hierarchy information.
        """
        try:
            self.status["text"] = "Scanning for media files..."
            self.root.update_idletasks()

            # Use the pre-loaded valid extensions
            valid_extensions = self.valid_extensions

            # Data structures to store our scan results
            folders_data = []  # List of MediaFolder tuples
            files_data = []    # List of MediaFile tuples

            # Assign unique IDs to folders as we encounter them
            folder_id_counter = 1
            folder_id_map = {}  # {folder_path: folder_id}

            processed_files = 0
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

                    # Add to folders_data
                    folders_data.append((folder_id_map[root], root, parent_id))

                # Process files in current folder
                for file in files:
                    processed_files += 1
                    if processed_files % 100 == 0:  # Update progress every 100 files
                        self.status["text"] = f"Scanning {processed_files} files, found {file_count} media files..."
                        self.root.update_idletasks()

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

            self.status["text"] = f"Scanned {processed_files} files, found {file_count} media files."
            return folders_data, files_data

        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan media: {e}")
            self.status["text"] = "Error scanning media."
            raise




    def save_to_db(self, folders_data, files_data):
        """
        Save folders and files to the database using pre-assigned IDs and parent relationships.
        """
        try:
            cur = self.conn.cursor()

            # Convert to tuples for batch insertion
            folders_tuples = folders_data  # Already tuples
            files_tuples = files_data      # Already tuples

            # Batch insert folders with their parent relationships
            if folders_tuples:
                self.status["text"] = f"Saving {len(folders_tuples)} folders to database..."
                self.root.update_idletasks()

                from psycopg2.extras import execute_values
                execute_values(
                    cur,
                    """
                    INSERT INTO media_folders (folder_id, folder_path, parent_folder_id)
                    VALUES %s
                    ON CONFLICT (folder_id) DO UPDATE
                    SET folder_path = EXCLUDED.folder_path,
                        parent_folder_id = EXCLUDED.parent_folder_id;
                    """,
                    folders_tuples,
                    template="(%s, %s, %s)",
                    page_size=100
                )

            # Batch insert files (without media_type)
            if files_tuples:
                self.status["text"] = f"Saving {len(files_tuples)} files to database..."
                self.root.update_idletasks()

                execute_values(
                    cur,
                    """
                    INSERT INTO media_files (folder_id, file_name, file_extension, file_size_kb, folder_path)
                    VALUES %s
                    ON CONFLICT (folder_id, file_name) DO UPDATE
                    SET file_extension = EXCLUDED.file_extension,
                        file_size_kb = EXCLUDED.file_size_kb;
                    """,
                    files_tuples,
                    template="(%s, %s, %s, %s, %s)",
                    page_size=100
                )

            self.conn.commit()
            self.status["text"] = f"Saved {len(files_tuples)} files to database."
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"Failed to save to database: {e}")
            self.status["text"] = "Error saving to database."
            raise


if __name__ == "__main__":
    try:
        conn = connect_to_db()
        root = tk.Tk()
        app = MediaManagerApp(root, conn)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
