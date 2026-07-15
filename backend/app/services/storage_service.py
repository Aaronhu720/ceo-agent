import uuid
from datetime import timedelta
from typing import BinaryIO

import boto3
from botocore.config import Config

from app.core.config import settings


class StorageService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.STORAGE_ENDPOINT,
                aws_access_key_id=settings.STORAGE_ACCESS_KEY,
                aws_secret_access_key=settings.STORAGE_SECRET_KEY,
                region_name=settings.STORAGE_REGION,
                config=Config(signature_version="s3v4"),
            )
        return self._client

    def ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=settings.STORAGE_BUCKET)
        except Exception:
            self.client.create_bucket(
                Bucket=settings.STORAGE_BUCKET,
                CreateBucketConfiguration={"LocationConstraint": settings.STORAGE_REGION},
            )

    def generate_presigned_upload(
        self,
        org_id: uuid.UUID,
        file_name: str,
        mime_type: str,
        expires_in: int = 3600,
    ) -> dict:
        file_id = uuid.uuid4()
        ext = file_name.rsplit(".", 1)[-1] if "." in file_name else ""
        storage_key = f"{org_id}/{file_id}.{ext}" if ext else f"{org_id}/{file_id}"

        url = self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.STORAGE_BUCKET,
                "Key": storage_key,
                "ContentType": mime_type,
            },
            ExpiresIn=expires_in,
        )

        return {
            "file_id": str(file_id),
            "upload_url": url,
            "storage_key": storage_key,
            "method": "PUT",
        }

    def generate_presigned_download(
        self,
        storage_key: str,
        expires_in: int = 3600,
        original_name: str | None = None,
    ) -> str:
        params = {
            "Bucket": settings.STORAGE_BUCKET,
            "Key": storage_key,
        }
        if original_name:
            params["ResponseContentDisposition"] = f'attachment; filename="{original_name}"'

        return self.client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
        )

    def upload_file(
        self,
        storage_key: str,
        file_obj: BinaryIO,
        mime_type: str,
    ):
        self.client.upload_fileobj(
            file_obj,
            settings.STORAGE_BUCKET,
            storage_key,
            ExtraArgs={"ContentType": mime_type},
        )

    def delete_file(self, storage_key: str):
        self.client.delete_object(
            Bucket=settings.STORAGE_BUCKET,
            Key=storage_key,
        )

    def get_file_url(self, storage_key: str) -> str:
        return f"{settings.STORAGE_PUBLIC_URL}/{storage_key}"


storage_service = StorageService()
