"""Storage abstraction for Federated Learning model weights (.pt files)."""
import os
import shutil
from typing import Protocol, runtime_checkable
from pathlib import Path


@runtime_checkable
class StorageBackend(Protocol):
    def save(self, local_path: str, remote_key: str) -> int:
        """Saves local file to storage at remote_key. Returns bytes written."""
        ...

    def load(self, remote_key: str, local_path: str) -> None:
        """Loads remote_key from storage into local_path."""
        ...

    def exists(self, remote_key: str) -> bool:
        """Checks if remote_key exists in storage."""
        ...

    def copy(self, src_key: str, dst_key: str) -> None:
        """Copies src_key to dst_key within storage."""
        ...

    def delete(self, remote_key: str) -> None:
        """Deletes remote_key from storage."""
        ...


class LocalFileStorage:
    def __init__(self, base_dir: str = "models"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _full_path(self, key: str) -> Path:
        clean_key = key.lstrip("/\\")
        return self.base_dir / clean_key

    def save(self, local_path: str, remote_key: str) -> int:
        dest = self._full_path(remote_key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, dest)
        return dest.stat().st_size

    def load(self, remote_key: str, local_path: str) -> None:
        src = self._full_path(remote_key)
        if not src.exists():
            raise FileNotFoundError(f"Model file '{remote_key}' not found in local storage ({src})")
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, local_path)

    def exists(self, remote_key: str) -> bool:
        return self._full_path(remote_key).exists()

    def copy(self, src_key: str, dst_key: str) -> None:
        src = self._full_path(src_key)
        if not src.exists():
            raise FileNotFoundError(f"Source model file '{src_key}' not found ({src})")
        dst = self._full_path(dst_key)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    def delete(self, remote_key: str) -> None:
        target = self._full_path(remote_key)
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        elif target.exists():
            target.unlink()


class GCSStorage:
    def __init__(self, bucket_name: str):
        from google.cloud import storage as gcs
        self.bucket_name = bucket_name
        self.client = gcs.Client()
        self.bucket = self.client.bucket(bucket_name)

    def _clean_key(self, key: str) -> str:
        return key.lstrip("/\\")

    def save(self, local_path: str, remote_key: str) -> int:
        blob = self.bucket.blob(self._clean_key(remote_key))
        blob.upload_from_filename(local_path)
        blob.reload()
        return blob.size or os.path.getsize(local_path)

    def load(self, remote_key: str, local_path: str) -> None:
        blob = self.bucket.blob(self._clean_key(remote_key))
        if not blob.exists():
            raise FileNotFoundError(f"Model file '{remote_key}' not found in GCS bucket '{self.bucket_name}'")
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(local_path)

    def exists(self, remote_key: str) -> bool:
        blob = self.bucket.blob(self._clean_key(remote_key))
        return blob.exists()

    def copy(self, src_key: str, dst_key: str) -> None:
        src_blob = self.bucket.blob(self._clean_key(src_key))
        if not src_blob.exists():
            raise FileNotFoundError(f"Source model '{src_key}' not found in GCS bucket '{self.bucket_name}'")
        self.bucket.copy_blob(src_blob, self.bucket, self._clean_key(dst_key))

    def delete(self, remote_key: str) -> None:
        # Check if it's a prefix/folder deletion
        clean = self._clean_key(remote_key)
        blobs = list(self.bucket.list_blobs(prefix=clean))
        if blobs:
            for b in blobs:
                b.delete()
        else:
            blob = self.bucket.blob(clean)
            if blob.exists():
                blob.delete()


def get_storage() -> StorageBackend:
    backend = os.getenv("STORAGE_BACKEND", "local").lower()
    if backend == "local":
        return LocalFileStorage(os.getenv("MODELS_DIR", "models"))
    if backend == "gcs":
        return GCSStorage(os.getenv("GCS_BUCKET", ""))
    raise ValueError(f"Unknown STORAGE_BACKEND: {backend}")
