# /app/classes/media_folder.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from .media_file import MediaFile  # Import MediaFile for type hints


@dataclass
class  CollectionManager:

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.collections: Dict[int, Collection] = db_manager.get_collections()

    def create_collection(self, collection_name: str) -> 'Collection':
        """Create a new collection"""
        # Implementation to create a new collection in the database

    def delete_collection(self, collection_id: int):
        self.db_manager.delete_collection(collection_id)

        pass

class Collection:
    collection_id: int
    collection_name: str
    media_files: List[MediaFile] = field(init=False, default_factory=list, repr=False)