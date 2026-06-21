import json
import os
from typing import Any, Dict, List, Optional
from pathlib import Path
from filelock import FileLock
from app.utils.logger import logger

class StorageManager:
    def __init__(self, file_path: str = "data/resources.json"):
        self.file_path = Path(file_path)
        self.lock_path = str(self.file_path) + ".lock"
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Ensures the storage directory and file exist with initial structure."""
        if not self.file_path.parent.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
        with FileLock(self.lock_path):
            if not self.file_path.exists():
                initial_data = {
                    "tables": {},
                    "files": {}
                }
                
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, indent=4)
                logger.info(f"Initialized new storage file at {self.file_path}")

    def _read_data(self) -> Dict[str, Any]:
        """Reads data from the JSON file. Assumes lock is held."""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_data(self, data: Dict[str, Any]):
        """Writes data to the JSON file. Assumes lock is held."""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def get_all(self) -> Dict[str, Any]:
        """Retrieves all data from storage."""
        with FileLock(self.lock_path):
            return self._read_data()

    def get_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Retrieves all records from a specific table."""
        with FileLock(self.lock_path):
            data = self._read_data()
            if "tables" not in data or table_name not in data["tables"]:
                raise ValueError(f"Table '{table_name}' not found.")
            return data["tables"][table_name]



    def update_record(self, table_name: str, update_data: List[Dict[str, Any]]) -> bool:
        """Overwrites the entire table with the new data."""
        with FileLock(self.lock_path):
            data = self._read_data()
            if "tables" not in data or table_name not in data["tables"]:
                raise ValueError(f"Table '{table_name}' not found.")
            
            data["tables"][table_name] = update_data
            self._write_data(data)
            logger.info(f"Updated table '{table_name}'")
            return True



    def get_file(self, file_name: str) -> Any:
        """Retrieves content of a specific file."""
        with FileLock(self.lock_path):
            data = self._read_data()
            if "files" not in data or file_name not in data["files"]:
                raise ValueError(f"File '{file_name}' not found.")
            return data["files"][file_name]



    def update_file(self, file_name: str, content: Any):
        """Updates content of an existing file."""
        with FileLock(self.lock_path):
            data = self._read_data()
            if "files" not in data or file_name not in data["files"]:
                raise ValueError(f"File '{file_name}' not found.")
            
            data["files"][file_name] = content
            self._write_data(data)
            logger.info(f"Updated file resource '{file_name}'")



# Create a singleton instance to be used by the application
storage = StorageManager()
