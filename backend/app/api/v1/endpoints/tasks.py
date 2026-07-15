from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter()


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    status_filter: str | None = None,
    priority: str | None = None,
    project_id: UUID | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Task).where(
        Task.organization_id == current_user.organization_id,
        Task.status != "cancelled",
    )
    if status_filter:
        query = query.where(Task.status == status_filter)
    if priority:
        query = query.where(Task.priority == priority)
    if project_id:
        query = query.where(Task.project_id == project_id)

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
        .offset(offset).limit(page_size)
    )
    return result.scalars().all()


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    req: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = Task(
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        **req.model_dump(),
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.organization_id == current_user.organization_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    req: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.organization_id == current_user.organization_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = req.model_dump(exclude_unset=True)
    if update_data.get("status") == "completed":
        update_data["completed_at"] = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(task, field, value)

    task.updated_by = current_user.id
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.organization_id == current_user.organization_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "cancelled"
    await db.commit()
    return {"success": True}
