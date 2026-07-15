import uuid as uuid_mod
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.file import File
from app.services.storage_service import storage_service
from app.services.audit_service import log_action

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/heic", "image/webp",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "video/mp4", "video/quicktime",
    "audio/mpeg", "audio/wav",
}


class PresignRequest(BaseModel):
    file_name: str
    mime_type: str
    file_size: int


class FileCompleteRequest(BaseModel):
    file_id: UUID
    storage_key: str
    checksum: str | None = None


@router.post("/presign")
async def presign_upload(
    req: PresignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if req.mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {req.mime_type}")

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if req.file_size > max_bytes:
        raise HTTPException(status_code=400, detail=f"File too large. Max: {settings.MAX_FILE_SIZE_MB}MB")

    presign_data = storage_service.generate_presigned_upload(
        org_id=current_user.organization_id,
        file_name=req.file_name,
        mime_type=req.mime_type,
    )

    file_record = File(
        id=uuid_mod.UUID(presign_data["file_id"]),
        organization_id=current_user.organization_id,
        uploaded_by=current_user.id,
        file_name=presign_data["storage_key"].split("/")[-1],
        original_file_name=req.file_name,
        mime_type=req.mime_type,
        file_size=req.file_size,
        storage_provider=settings.STORAGE_PROVIDER,
        storage_bucket=settings.STORAGE_BUCKET,
        storage_key=presign_data["storage_key"],
        processing_status="uploading",
    )
    db.add(file_record)
    await db.commit()

    return presign_data


@router.post("/complete")
async def complete_upload(
    req: FileCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(File).where(
            File.id == req.file_id,
            File.organization_id == current_user.organization_id,
        )
    )
    file_record = result.scalar_one_or_none()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    file_record.storage_key = req.storage_key
    file_record.checksum = req.checksum
    file_record.processing_status = "pending"

    await log_action(
        db,
        organization_id=current_user.organization_id,
        action="file.uploaded",
        resource_type="file",
        resource_id=file_record.id,
        user_id=current_user.id,
        after_json={"file_name": file_record.original_file_name, "size": file_record.file_size},
    )

    await db.commit()

    # TODO: dispatch Celery task for thumbnail generation, OCR, text extraction

    return {"success": True, "file_id": str(file_record.id)}


@router.get("")
async def list_files(
    mime_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(File).where(
        File.organization_id == current_user.organization_id,
        File.processing_status != "deleted",
    )
    if mime_type:
        query = query.where(File.mime_type.startswith(mime_type))

    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(File.created_at.desc()).offset(offset).limit(page_size))
    files = result.scalars().all()

    return [
        {
            "id": str(f.id),
            "file_name": f.file_name,
            "original_file_name": f.original_file_name,
            "mime_type": f.mime_type,
            "file_size": f.file_size,
            "processing_status": f.processing_status,
            "preview_url": f.preview_url,
            "created_at": f.created_at.isoformat(),
        }
        for f in files
    ]


@router.get("/{file_id}")
async def get_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.organization_id == current_user.organization_id,
        )
    )
    f = result.scalar_one_or_none()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")

    download_url = storage_service.generate_presigned_download(
        f.storage_key, original_name=f.original_file_name
    )

    return {
        "id": str(f.id),
        "file_name": f.file_name,
        "original_file_name": f.original_file_name,
        "mime_type": f.mime_type,
        "file_size": f.file_size,
        "storage_key": f.storage_key,
        "download_url": download_url,
        "processing_status": f.processing_status,
        "extracted_text": f.extracted_text,
        "created_at": f.created_at.isoformat(),
    }


@router.delete("/{file_id}")
async def delete_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.organization_id == current_user.organization_id,
        )
    )
    f = result.scalar_one_or_none()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")

    f.processing_status = "deleted"

    await log_action(
        db,
        organization_id=current_user.organization_id,
        action="file.deleted",
        resource_type="file",
        resource_id=f.id,
        user_id=current_user.id,
    )

    await db.commit()
    return {"success": True}
