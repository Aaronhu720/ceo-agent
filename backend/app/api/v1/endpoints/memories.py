from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.memory import Memory
from app.schemas.memory import MemoryCreate, MemoryUpdate, MemoryResponse, MemorySearchRequest

router = APIRouter()


@router.get("", response_model=list[MemoryResponse])
async def list_memories(
    memory_type: str | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Memory).where(Memory.organization_id == current_user.organization_id)
    if memory_type:
        query = query.where(Memory.memory_type == memory_type)
    if status_filter:
        query = query.where(Memory.status == status_filter)
    else:
        query = query.where(Memory.status != "archived")

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Memory.importance_score.desc(), Memory.created_at.desc())
        .offset(offset).limit(page_size)
    )
    return result.scalars().all()


@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    req: MemoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memory = Memory(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        memory_type=req.memory_type,
        title=req.title,
        content=req.content,
        summary=req.summary,
        importance_score=req.importance_score,
        confidence_score=req.confidence_score,
        sensitivity_level=req.sensitivity_level,
        valid_until=req.valid_until,
        status="proposed",
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return memory


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Memory).where(
            Memory.id == memory_id,
            Memory.organization_id == current_user.organization_id,
        )
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.patch("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: UUID,
    req: MemoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Memory).where(
            Memory.id == memory_id,
            Memory.organization_id == current_user.organization_id,
        )
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(memory, field, value)

    await db.commit()
    await db.refresh(memory)
    return memory


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Memory).where(
            Memory.id == memory_id,
            Memory.organization_id == current_user.organization_id,
        )
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    memory.status = "archived"
    await db.commit()
    return {"success": True}


@router.post("/{memory_id}/confirm", response_model=MemoryResponse)
async def confirm_memory(
    memory_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Memory).where(
            Memory.id == memory_id,
            Memory.organization_id == current_user.organization_id,
        )
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    memory.status = "confirmed"
    memory.confirmed_by_user = True
    await db.commit()
    await db.refresh(memory)
    return memory


@router.post("/{memory_id}/reject", response_model=MemoryResponse)
async def reject_memory(
    memory_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Memory).where(
            Memory.id == memory_id,
            Memory.organization_id == current_user.organization_id,
        )
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    memory.status = "rejected"
    await db.commit()
    await db.refresh(memory)
    return memory


@router.post("/search", response_model=list[MemoryResponse])
async def search_memories(
    req: MemorySearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Memory).where(
        Memory.organization_id == current_user.organization_id,
        Memory.status.in_(["proposed", "confirmed"]),
        Memory.content.icontains(req.query),
    )
    if req.memory_types:
        query = query.where(Memory.memory_type.in_(req.memory_types))

    result = await db.execute(query.order_by(Memory.importance_score.desc()).limit(req.limit))
    return result.scalars().all()
