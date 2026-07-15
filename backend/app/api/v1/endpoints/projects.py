from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project import Project, ProjectUpdate as ProjectUpdateModel
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectUpdateCreate, ProjectUpdateResponse,
)

router = APIRouter()


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Project).where(
        Project.organization_id == current_user.organization_id,
        Project.status != "deleted",
    )
    if status_filter:
        query = query.where(Project.status == status_filter)

    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(Project.created_at.desc()).offset(offset).limit(page_size))
    return result.scalars().all()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    req: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = Project(
        organization_id=current_user.organization_id,
        owner_id=current_user.id,
        created_by=current_user.id,
        **req.model_dump(),
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == current_user.organization_id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    req: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == current_user.organization_id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    project.updated_by = current_user.id
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}/updates", response_model=list[ProjectUpdateResponse])
async def list_project_updates(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == current_user.organization_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(ProjectUpdateModel)
        .where(ProjectUpdateModel.project_id == project_id)
        .order_by(ProjectUpdateModel.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{project_id}/updates", response_model=ProjectUpdateResponse, status_code=status.HTTP_201_CREATED)
async def create_project_update(
    project_id: UUID,
    req: ProjectUpdateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == current_user.organization_id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update = ProjectUpdateModel(
        project_id=project_id,
        created_by=current_user.id,
        **req.model_dump(),
    )
    db.add(update)

    if req.progress_percent is not None:
        project.progress_percent = req.progress_percent
    if req.risk_level is not None:
        project.risk_level = req.risk_level

    await db.commit()
    await db.refresh(update)
    return update
