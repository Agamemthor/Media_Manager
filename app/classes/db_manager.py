from tkinter import messagebox
import psycopg2
from psycopg2 import OperationalError
from .media_file import MediaFile
from .media_folder import MediaFolder

class DBManager:
    def __init__(self, conn_config):
        self.dbname = conn_config['dbname']
        self.user = conn_config['user']
        self.password = conn_config['password']
        self.host = conn_config['host']
        self.port = conn_config['port']
        self.retries = conn_config['retries']
        self.delay = conn_config['delay']
        self.conn = None
        self.connect()

    def connect(self):
        import time
        for i in range(self.retries):
            try:
                self.conn = psycopg2.connect(
                    dbname=self.dbname,
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port
                )
                print("Connected to PostgreSQL!")
                return self.conn
            except OperationalError as e:
                print(f"Connection attempt {i + 1} failed: {e}")
                if i < self.retries - 1:
                    time.sleep(self.delay)
        raise Exception("Could not connect to PostgreSQL after several retries.")
    
    def get_folders_from_db(self):
        cur = self.get_cursor()
        cur.execute("""
            SELECT folder_id, folder_path, parent_folder_id
            FROM media_folders
            ORDER BY folder_path
        """)
        return cur.fetchall()
    
    def get_files_from_db(self):
        cur = self.get_cursor()
        cur.execute("""
            SELECT folder_id, file_name, file_extension, file_size_kb, folder_path
            FROM media_files
            ORDER BY folder_path, file_name
        """)
        return cur.fetchall()

    def get_cursor(self):
        if self.conn is None:
            self.connect()
        return self.conn.cursor()

    def commit(self):
        if self.conn:
            self.conn.commit()

    def rollback(self):
        if self.conn:
            self.conn.rollback()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
    

    def load_media_type_mappings(self):
        """Load media type mappings from the database"""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT media_type_extension, media_type_description FROM media_types;")
            extension_to_type = {row[0].lower(): row[1] for row in cur.fetchall()}
            self.extension_to_type = extension_to_type
            valid_extensions = set(self.extension_to_type.keys())
            return extension_to_type, valid_extensions  
        except Exception as e:
            print(f"Error loading media type mappings: {e}")
            extension_to_type = {}
            valid_extensions = set()
            return extension_to_type, valid_extensions 
        
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