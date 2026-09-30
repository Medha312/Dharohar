import os
import shutil
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Union

from app.core.config import get_settings

settings = get_settings()


class BaseStorageService(ABC):
    @abstractmethod
    def save_file(
        self,
        file_data: Union[bytes, BinaryIO],
        destination_filename: str,
        subfolder: str = "documents",
    ) -> str:
        """Saves file and returns relative storage path / key."""
        pass

    @abstractmethod
    def get_file_bytes(self, storage_path: str) -> bytes:
        """Retrieves raw file bytes."""
        pass

    @abstractmethod
    def get_absolute_path(self, storage_path: str) -> Path:
        """Returns local absolute path for direct file reading/processing."""
        pass

    @abstractmethod
    def delete_file(self, storage_path: str) -> bool:
        """Deletes file from storage."""
        pass


class LocalStorageService(BaseStorageService):
    def __init__(self, base_dir: str = settings.STORAGE_DIR):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_file(
        self,
        file_data: Union[bytes, BinaryIO],
        destination_filename: str,
        subfolder: str = "documents",
    ) -> str:
        folder = self.base_dir / subfolder
        folder.mkdir(parents=True, exist_ok=True)

        unique_prefix = uuid.uuid4().hex[:8]
        safe_name = f"{unique_prefix}_{destination_filename}"
        target_path = folder / safe_name

        if isinstance(file_data, bytes):
            with open(target_path, "wb") as f:
                f.write(file_data)
        else:
            with open(target_path, "wb") as f:
                shutil.copyfileobj(file_data, f)

        # Return relative storage path
        return str(Path(subfolder) / safe_name).replace("\\", "/")

    def get_file_bytes(self, storage_path: str) -> bytes:
        abs_path = self.get_absolute_path(storage_path)
        with open(abs_path, "rb") as f:
            return f.read()

    def get_absolute_path(self, storage_path: str) -> Path:
        clean_path = storage_path.lstrip("/\\")
        return (self.base_dir / clean_path).resolve()

    def delete_file(self, storage_path: str) -> bool:
        try:
            abs_path = self.get_absolute_path(storage_path)
            if abs_path.exists() and abs_path.is_file():
                abs_path.unlink()
                return True
            return False
        except Exception:
            return False


storage_service = LocalStorageService()
