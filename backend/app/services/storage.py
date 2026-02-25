"""
File storage service supporting local filesystem and S3-compatible storage.
"""
import os
import io
import logging
from typing import BinaryIO, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Abstraction over local and S3-compatible file storage."""

    def __init__(self):
        self.backend = settings.storage_backend
        self._s3_client = None

    @property
    def s3_client(self):
        if self._s3_client is None:
            import boto3
            self._s3_client = boto3.client(
                's3',
                region_name=settings.s3_region,
                endpoint_url=settings.s3_endpoint_url or None,
                aws_access_key_id=settings.s3_access_key_id,
                aws_secret_access_key=settings.s3_secret_access_key,
            )
        return self._s3_client

    async def upload_file(self, file_data: bytes | BinaryIO, key: str, content_type: str = "application/octet-stream") -> str:
        """Upload a file and return its storage key."""
        if self.backend == "s3":
            if isinstance(file_data, bytes):
                file_data = io.BytesIO(file_data)
            self.s3_client.upload_fileobj(
                file_data, settings.s3_bucket_name, key,
                ExtraArgs={"ContentType": content_type}
            )
            logger.info(f"Uploaded to S3: {key}")
            return key
        else:
            # Local storage
            local_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
            os.makedirs(local_dir, exist_ok=True)
            file_path = os.path.join(local_dir, key)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if isinstance(file_data, bytes):
                with open(file_path, 'wb') as f:
                    f.write(file_data)
            else:
                with open(file_path, 'wb') as f:
                    f.write(file_data.read())
            logger.info(f"Saved locally: {file_path}")
            return key

    async def download_file(self, key: str) -> bytes:
        """Download a file by key and return its contents."""
        if self.backend == "s3":
            response = self.s3_client.get_object(Bucket=settings.s3_bucket_name, Key=key)
            return response['Body'].read()
        else:
            local_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
            file_path = os.path.join(local_dir, key)
            with open(file_path, 'rb') as f:
                return f.read()

    async def file_exists(self, key: str) -> bool:
        """Check if a file exists."""
        if self.backend == "s3":
            try:
                self.s3_client.head_object(Bucket=settings.s3_bucket_name, Key=key)
                return True
            except Exception:
                return False
        else:
            local_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
            return os.path.exists(os.path.join(local_dir, key))

    async def delete_file(self, key: str) -> bool:
        """Delete a file by key."""
        if self.backend == "s3":
            try:
                self.s3_client.delete_object(Bucket=settings.s3_bucket_name, Key=key)
                return True
            except Exception:
                return False
        else:
            local_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
            file_path = os.path.join(local_dir, key)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False

    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """Get a presigned URL for direct download (S3 only)."""
        if self.backend == "s3":
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.s3_bucket_name, 'Key': key},
                ExpiresIn=expires_in,
            )
        return None


# Singleton instance
storage = StorageService()
