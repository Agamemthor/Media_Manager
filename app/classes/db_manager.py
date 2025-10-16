import psycopg2
from psycopg2 import OperationalError
from psycopg2.extras import execute_values
from tkinter import messagebox
import logging
from typing import List, Tuple, Set, Dict, Optional
from .media_file import MediaFile
from .media_folder import MediaFolder

logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self, conn_config, set_status):
        self.set_status = set_status
        self.conn_config = conn_config
        self.conn = None
        self.connect()

    def connect(self):
        """Connect to the PostgreSQL database."""
        for i in range(self.conn_config["retries"]):
            try:
                self.conn = psycopg2.connect(
                    dbname=self.conn_config['dbname'],
                    user=self.conn_config['user'],
                    password=self.conn_config['password'],
                    host=self.conn_config['host'],
                    port=self.conn_config['port']
                )
                logger.info("Connected to PostgreSQL!")
                return
            except OperationalError as e:
                logger.error(f"Connection attempt {i + 1} failed: {e}")
                if i < self.conn_config["retries"] - 1:
                    import time
                    time.sleep(self.conn_config["delay"])
        raise Exception("Could not connect to PostgreSQL after several retries.")

    def get_folders_from_db(self) -> List[Tuple]:
        """Get folders from the database."""
        try:
            with self.get_cursor() as cur:
                cur.execute(
                    """
                    SELECT folder_id, folder_path, parent_folder_id
                    FROM media_folders
                    ORDER BY folder_path
                    """
                )
                return cur.fetchall()
        except Exception as e:
            logger.exception("Failed to get folders from database")
            raise

    def get_files_from_db(self) -> List[Tuple]:
        """Get files from the database."""
        try:
            with self.get_cursor() as cur:
                cur.execute(
                    """
                    SELECT folder_id, file_name, file_extension, file_size_kb, folder_path
                    FROM media_files
                    ORDER BY folder_path, file_name
                    """
                )
                return cur.fetchall()
        except Exception as e:
            logger.exception("Failed to get files from database")
            raise

    def get_cursor(self):
        """Get a database cursor."""
        if self.conn is None:
            self.connect()
        return self.conn.cursor()

    def commit(self):
        """Commit the current transaction."""
        if self.conn:
            self.conn.commit()

    def rollback(self):
        """Rollback the current transaction."""
        if self.conn:
            self.conn.rollback()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def load_media_type_mappings(self) -> Tuple[Dict[str, str], Set[str]]:
        """Load media type mappings from the database."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT media_type_extension, media_type_description FROM media_types;")
                extension_to_type = {row[0].lower(): row[1] for row in cur.fetchall()}
                valid_extensions = set(extension_to_type.keys())
                return extension_to_type, valid_extensions
        except Exception as e:
            logger.exception("Error loading media type mappings")
            return {}, set()

    def save_to_db(self, folders_data: List[Tuple], files_data: List[Tuple]):
        """Save folders and files to the database."""
        try:
            with self.conn.cursor() as cur:
                if folders_data:
                    self.set_status(f"Saving {len(folders_data)} folders to database...")
                    execute_values(
                        cur,
                        """
                        INSERT INTO media_folders (folder_id, folder_path, parent_folder_id)
                        VALUES %s
                        ON CONFLICT (folder_id) DO UPDATE
                        SET folder_path = EXCLUDED.folder_path,
                            parent_folder_id = EXCLUDED.parent_folder_id;
                        """,
                        folders_data,
                        template="(%s, %s, %s)",
                        page_size=100,
                    )

                if files_data:
                    self.set_status(f"Saving {len(files_data)} files to database...")
                    execute_values(
                        cur,
                        """
                        INSERT INTO media_files (folder_id, file_name, file_extension, file_size_kb, folder_path)
                        VALUES %s
                        ON CONFLICT (folder_id, file_name) DO UPDATE
                        SET file_extension = EXCLUDED.file_extension,
                            file_size_kb = EXCLUDED.file_size_kb;
                        """,
                        files_data,
                        template="(%s, %s, %s, %s, %s)",
                        page_size=100,
                    )
                self.conn.commit()
                self.set_status(f"Saved {len(files_data)} files to database.")
        except Exception as e:
            self.conn.rollback()
            logger.exception("Failed to save to database")
            self.set_status("Error saving to database.")
            raise

    def delete_folders_and_files(self, folder_ids: Set[int]):
        """Delete folders and their associated files from the database."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM media_files
                    WHERE folder_id = ANY(%s);
                    """,
                    (list(folder_ids),),
                )
                cur.execute(
                    """
                    DELETE FROM media_folders
                    WHERE folder_id = ANY(%s);
                    """,
                    (list(folder_ids),),
                )
        except Exception as e:
            self.conn.rollback()
            logger.exception("Failed to delete folders and files")
            raise
