from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.approval import Approval

router = APIRouter()


@router.get("")
async def list_approvals(
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Approval).where(
        Approval.organization_id == current_user.organization_id,
        Approval.requested_for_user_id == current_user.id,
    )
    if status_filter:
        query = query.where(Approval.status == status_filter)

    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(Approval.created_at.desc()).offset(offset).limit(page_size))
    approvals = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "action_type": a.action_type,
            "action_description": a.action_description,
            "payload_json": a.payload_json,
            "risk_level": a.risk_level,
            "status": a.status,
            "created_at": a.created_at.isoformat(),
            "expires_at": a.expires_at.isoformat() if a.expires_at else None,
        }
        for a in approvals
    ]


@router.get("/{approval_id}")
async def get_approval(
    approval_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Approval).where(
            Approval.id == approval_id,
            Approval.organization_id == current_user.organization_id,
        )
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    return {
        "id": str(approval.id),
        "action_type": approval.action_type,
        "action_description": approval.action_description,
        "payload_json": approval.payload_json,
        "risk_level": approval.risk_level,
        "status": approval.status,
        "created_at": approval.created_at.isoformat(),
    }


@router.post("/{approval_id}/approve")
async def approve(
    approval_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Approval).where(
            Approval.id == approval_id,
            Approval.organization_id == current_user.organization_id,
        )
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    approval.status = "approved"
    approval.approved_at = datetime.now(timezone.utc)
    await db.commit()
    return {"success": True}


@router.post("/{approval_id}/reject")
async def reject(
    approval_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Approval).where(
            Approval.id == approval_id,
            Approval.organization_id == current_user.organization_id,
        )
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    approval.status = "rejected"
    approval.rejected_at = datetime.now(timezone.utc)
    await db.commit()
    return {"success": True}
