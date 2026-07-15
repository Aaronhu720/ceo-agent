from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.decision import Decision
from app.schemas.decision import DecisionCreate, DecisionUpdate, DecisionResponse

router = APIRouter()


@router.get("", response_model=list[DecisionResponse])
async def list_decisions(
    decision_status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Decision).where(Decision.organization_id == current_user.organization_id)
    if decision_status:
        query = query.where(Decision.decision_status == decision_status)

    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(Decision.created_at.desc()).offset(offset).limit(page_size))
    return result.scalars().all()


@router.post("", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
async def create_decision(
    req: DecisionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    decision = Decision(
        organization_id=current_user.organization_id,
        **req.model_dump(),
    )
    db.add(decision)
    await db.commit()
    await db.refresh(decision)
    return decision


@router.get("/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    decision_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Decision).where(
            Decision.id == decision_id,
            Decision.organization_id == current_user.organization_id,
        )
    )
    decision = result.scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@router.patch("/{decision_id}", response_model=DecisionResponse)
async def update_decision(
    decision_id: UUID,
    req: DecisionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Decision).where(
            Decision.id == decision_id,
            Decision.organization_id == current_user.organization_id,
        )
    )
    decision = result.scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(decision, field, value)

    await db.commit()
    await db.refresh(decision)
    return decision


@router.post("/{decision_id}/approve", response_model=DecisionResponse)
async def approve_decision(
    decision_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Decision).where(
            Decision.id == decision_id,
            Decision.organization_id == current_user.organization_id,
        )
    )
    decision = result.scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    decision.decision_status = "approved"
    decision.decided_by = current_user.id
    decision.decided_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(decision)
    return decision


@router.post("/{decision_id}/review", response_model=DecisionResponse)
async def review_decision(
    decision_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Decision).where(
            Decision.id == decision_id,
            Decision.organization_id == current_user.organization_id,
        )
    )
    decision = result.scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    decision.decision_status = "under_review"
    await db.commit()
    await db.refresh(decision)
    return decision
