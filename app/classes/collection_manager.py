from dataclasses import dataclass, field
from typing import Dict, List
import logging
from .media_file import MediaFile

logger = logging.getLogger(__name__)

@dataclass
class Collection:
    collection_id: int
    collection_name: str
    media_files: List[MediaFile] = field(default_factory=list, repr=False)

@dataclass
class CollectionManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.collections: Dict[int, Collection] = db_manager.get_collections()

    def create_collection(self, collection_name: str) -> Collection:
        """Create a new collection."""
        try:
            return self.db_manager.create_collection(collection_name)
        except Exception as e:
            logger.exception("Failed to create collection")
            raise

    def delete_collection(self, collection_id: int):
        """Delete a collection."""
        try:
            self.db_manager.delete_collection(collection_id)
        except Exception as e:
            logger.exception("Failed to delete collection")
            raise
