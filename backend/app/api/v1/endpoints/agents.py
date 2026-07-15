from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.agent import Agent, AgentRun

router = APIRouter()


@router.get("")
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Agent).where(
            Agent.organization_id == current_user.organization_id,
            Agent.status == "active",
        ).order_by(Agent.created_at.desc())
    )
    agents = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "name": a.name,
            "agent_type": a.agent_type,
            "description": a.description,
            "model_provider": a.model_provider,
            "model_name": a.model_name,
            "status": a.status,
        }
        for a in agents
    ]


@router.get("/{agent_id}")
async def get_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.organization_id == current_user.organization_id,
        )
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "id": str(agent.id),
        "name": agent.name,
        "agent_type": agent.agent_type,
        "description": agent.description,
        "system_instructions": agent.system_instructions,
        "model_provider": agent.model_provider,
        "model_name": agent.model_name,
        "temperature": agent.temperature,
        "tools_json": agent.tools_json,
        "permissions_json": agent.permissions_json,
        "status": agent.status,
        "version": agent.version,
    }


@router.get("/runs/{run_id}")
async def get_agent_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AgentRun).where(
            AgentRun.id == run_id,
            AgentRun.organization_id == current_user.organization_id,
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    return {
        "id": str(run.id),
        "agent_id": str(run.agent_id),
        "trigger_type": run.trigger_type,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "input_json": run.input_json,
        "output_json": run.output_json,
        "token_usage_json": run.token_usage_json,
        "cost": run.cost,
        "steps": [
            {
                "id": str(s.id),
                "step_number": s.step_number,
                "step_type": s.step_type,
                "tool_name": s.tool_name,
                "status": s.status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in run.steps
        ],
    }
