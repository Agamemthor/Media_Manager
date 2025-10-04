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

        self.tree = ttk.Treeview(self.root, columns=("Type", "Size", "Path"), show="tree headings")
        self.tree.heading("#0", text="Name")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Size", text="Size (KB)")
        self.tree.heading("Path", text="Path")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.tag_configure("folder", foreground="blue")
        self.tree.tag_configure("file", foreground="black")

        # Create a menubar
        self.menubar = tk.Menu(root)
        self.root.config(menu=self.menubar)

        # Add a "File" menu
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="Select New Root Folder", command=self.change_rootfolder)
        self.menubar.add_cascade(label="File", menu=self.file_menu)

        # Add a status label at the bottom
        self.status = ttk.Label(self.root, text="Ready", anchor="w")
        self.status.pack(fill=tk.X, padx=5, pady=2)

        self.rootfolder = self.get_rootfolder()
        self.root.title(self.rootfolder)
        
        self.populate_treeview()

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

            # Scan the new root folder
            self.status["text"] = "Scanning new root folder..."
            self.root.update_idletasks()
            df = self.scan_media(self.rootfolder)
            if not df.empty:
                self.save_to_db(df)

            # Refresh the treeview
            self.populate_treeview()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to change root folder: {e}")
            self.status["text"] = "Error"

    def scan_media(self, folder_path):
        # Fetch valid extensions once
        cur = self.conn.cursor()
        cur.execute("SELECT Media_Type_Extension FROM Media_Types;")
        valid_extensions = {row[0].lower() for row in cur.fetchall()}

        # Scan files and show real-time count
        data = []
        total_files = 0
        matched_files = 0

        for root, _, files in os.walk(folder_path):
            for file in files:
                total_files += 1
                ext = os.path.splitext(file)[1].lower()
                if ext in valid_extensions:
                    matched_files += 1
                    full_path = os.path.join(root, file)
                    size = os.path.getsize(full_path) // 1024
                    data.append({
                        "folder_path": root,
                        "file_name": file,
                        "file_extension": ext,
                        "file_size_kb": size,
                    })

                # Update status every 10 files to avoid UI lag
                if total_files % 50 == 0:
                    self.status["text"] = f"Scanned {total_files} files, found {matched_files} media files..."
                    self.root.update_idletasks()  # Force UI update

        self.status["text"] = f"Done! Scanned {total_files} files, found {matched_files} media files."
        return pd.DataFrame(data)

    def populate_treeview(self):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM media_files;")
            if cur.fetchone()[0] == 0:
                if messagebox.askyesno("Scan Media", "No media data found. Scan now?"):
                    self.status["text"] = "Scanning for media files..."
                    self.root.update_idletasks()
                    df = self.scan_media(self.rootfolder)
                    if not df.empty:
                        self.save_to_db(df)

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            self.status["text"] = "Reading media files from database..."
            self.root.update_idletasks()
            
            # Fetch all files using the view
            df = pd.read_sql("""
                SELECT file_name, media_type_description, file_size_kb, folder_path
                FROM media_files_extended
                ORDER BY folder_path, file_name;
            """, self.conn)

            # Build a hierarchy dictionary
            hierarchy = {}

            self.status["text"] = "Building tree hierarchy..."
            self.root.update_idletasks()

            processed_files=0
            total_files = len(df.index)
            for _, row in df.iterrows():
                folder_path = row["folder_path"]

                # Remove the rootfolder prefix and split into parts
                if not folder_path.startswith(self.rootfolder):
                    print(f"Warning: Folder path {folder_path} doesn't start with rootfolder {self.rootfolder}")
                    continue

                relative_path = folder_path.replace(self.rootfolder, "").strip(os.sep)
                if not relative_path:  # File is directly in rootfolder
                    parts = []
                else:
                    parts = [p for p in relative_path.split(os.sep) if p]  # Remove empty parts

                # Start from the root of our hierarchy
                current_level = hierarchy

                # Build the hierarchy path by path
                for part in parts:
                    if part not in current_level:
                        current_level[part] = {"subfolders": {}, "files": []}
                    current_level = current_level[part]["subfolders"]

                # Ensure current_level has a "files" key (defensive programming)
                if "files" not in current_level:
                    current_level["files"] = []

                # Add the file to the deepest folder
                current_level["files"].append({
                    "name": row["file_name"],
                    "type": row["media_type_description"],
                    "size": row["file_size_kb"],
                    "path": folder_path
                })

                processed_files+=1
                # Update status every 100 files to avoid UI lag
                if processed_files % 100 == 0:
                    self.status["text"] = f"Building tree hierarchy... Processed {processed_files} files out of {total_files} files..."
                    self.root.update_idletasks()  # Force UI update

            # Recursively add folders and files to the treeview
            def add_to_tree(parent_node, node):
                # Add subfolders (sorted alphabetically)
                for folder_name in sorted(node.get("subfolders", {}).keys()):
                    folder_node = self.tree.insert(
                        parent_node, "end",
                        text=folder_name,
                        open=False,
                        tags=("folder",)
                    )
                    add_to_tree(folder_node, node["subfolders"][folder_name])

                # Add files (sorted alphabetically)
                for file_info in sorted(node.get("files", []), key=lambda x: x["name"]):
                    self.tree.insert(
                        parent_node, "end",
                        text=file_info["name"],
                        values=(
                            file_info["type"],
                            file_info["size"],
                            file_info["path"]
                        ),
                        tags=("file",)
                    )

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Add root folder
            root_node = self.tree.insert(
                "", "end",
                text=os.path.basename(self.rootfolder),
                open=True,
                tags=("folder",)
            )

            # Add the hierarchy to the treeview
            if hierarchy:  # Only add if we have data
                add_to_tree(root_node, hierarchy)

            # Add right-click menu binding
            self.tree.bind("<Button-3>", self.show_context_menu)

            self.status["text"] = "Ready"
        except Exception as e:
            import traceback
            print(f"Error in populate_treeview: {e}")
            print(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to populate treeview: {e}")
            self.status["text"] = "Error"

    def show_context_menu(self, event):
        # Identify the item under the cursor
        item = self.tree.identify_row(event.y)
        if not item:
            return

        # Create a context menu
        menu = tk.Menu(self.root, tearoff=0)

        # Add "Show in Folder" option
        menu.add_command(
            label="Show in Folder",
            command=lambda: self.open_in_explorer(item)
        )

        # Add "Scripts" submenu
        scripts_menu = tk.Menu(menu, tearoff=0)
        scripts_menu.add_command(
            label="Run Script 1",
            command=lambda: self.run_script(item, "script1.py")
        )
        scripts_menu.add_command(
            label="Run Script 2",
            command=lambda: self.run_script(item, "script2.py")
        )
        menu.add_cascade(label="Scripts", menu=scripts_menu)

        # Post the menu and bind it to close when clicked outside
        menu.post(event.x_root, event.y_root)
        menu.bind("<FocusOut>", lambda e: menu.unpost())  # Dismiss on focus loss
        menu.bind("<Leave>", lambda e: menu.unpost())     # Dismiss on mouse leave

    def open_in_explorer(self, item):
        try:
            item_text = self.tree.item(item)["text"]
            values = self.tree.item(item)["values"]
 
            if values:  # This is a file
                path = values[2]  # folder_path from values
            else:  # This is a folder
                # Reconstruct the full path by traversing up the tree
                path_parts = [item_text]
                parent = self.tree.parent(item)
                while parent:
                    parent_text = self.tree.item(parent)["text"]
                    path_parts.insert(0, parent_text)
                    parent = self.tree.parent(parent)
                path = os.path.join(self.rootfolder, *path_parts)
            # Open in system file explorer
            if os.path.exists(path):
                if platform.system() == "Windows":
                    os.startfile(path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", path])
                else:  # Linux
                    subprocess.run(["xdg-open", path])
            else:
                messagebox.showerror("Error", f"Path not found: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open path: {e}")

    def run_script(self, item, script_name):
        try:
            # Get the folder path for the clicked item
            values = self.tree.item(item)["values"]
            if values:  # This is a file
                folder_path = values[2]  # folder_path from values
            else:  # This is a folder
                # Reconstruct the full path by traversing up the tree
                item_text = self.tree.item(item)["text"]
                path_parts = [item_text]
                parent = self.tree.parent(item)
                while parent:
                    parent_text = self.tree.item(parent)["text"]
                    path_parts.insert(0, parent_text)
                    parent = self.tree.parent(parent)
                folder_path = os.path.join(self.rootfolder, *path_parts)

            # Run the script with the folder path as an argument
            script_path = os.path.join("scripts", script_name)  # Assume scripts are in a "scripts" folder
            if os.path.exists(script_path):
                subprocess.run([sys.executable, script_path, folder_path], check=True)
                messagebox.showinfo("Success", f"Script {script_name} executed successfully!")
            else:
                messagebox.showerror("Error", f"Script not found: {script_path}")

        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Script failed: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")


    def save_to_db(self, df):
        try:
            cur = self.conn.cursor()
            total_files = len(df)
            self.status["text"] = f"Saving 0/{total_files} files to database..."
            self.root.update_idletasks()

            # Step 1: Bulk-insert all unique folders
            unique_folders = df["folder_path"].unique()
            if len(unique_folders) > 0:
                from psycopg2.extras import execute_values
                execute_values(
                    cur,
                    """
                    INSERT INTO media_folders (folder_path)
                    VALUES %s
                    ON CONFLICT (folder_path) DO NOTHING;
                    """,
                    [(folder_path,) for folder_path in unique_folders],
                    template="(%s)",
                    page_size=100
                )

            # Step 2: Fetch all folder IDs
            if len(unique_folders) > 0:
                cur.execute(
                    f"SELECT folder_path, folder_id FROM media_folders WHERE folder_path = ANY(%s);",
                    (list(unique_folders),)
                )
                folder_id_map = {row[0]: row[1] for row in cur.fetchall()}

            # Step 3: Bulk-insert all files with progress
            if not df.empty:
                file_data = []
                for idx, (_, row) in enumerate(df.iterrows(), 1):
                    folder_id = folder_id_map.get(row["folder_path"])
                    if folder_id is not None:
                        file_data.append((
                            folder_id,
                            row["file_name"],
                            row["file_extension"],
                            row["file_size_kb"]
                        ))

                    # Update progress every 10 files
                    if idx % 10 == 0:
                        self.status["text"] = f"Saving {idx}/{total_files} files..."
                        self.root.update_idletasks()

                if file_data:
                    execute_values(
                        cur,
                        """
                        INSERT INTO media_files (folder_id, file_name, file_extension, file_size_kb)
                        VALUES %s
                        ON CONFLICT DO NOTHING;
                        """,
                        file_data,
                        template="(%s, %s, %s, %s)",
                        page_size=100
                    )

            self.conn.commit()
            self.status["text"] = f"Saved {len(df)} files to database."
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
