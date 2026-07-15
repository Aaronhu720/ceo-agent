"""Add Code Agent (Claude) to existing database."""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.agent import Agent
from app.models.organization import Organization


async def add_code_agent():
    async with AsyncSessionLocal() as db:
        org_result = await db.execute(select(Organization).limit(1))
        org = org_result.scalar_one_or_none()
        if not org:
            print("No organization found")
            return

        existing = await db.execute(
            select(Agent).where(Agent.agent_type == "code", Agent.organization_id == org.id)
        )
        if existing.scalar_one_or_none():
            print("Code Agent already exists")
            return

        code_agent = Agent(
            organization_id=org.id,
            name="Code Agent",
            agent_type="code",
            description="AI programming assistant powered by Claude",
            system_instructions="You are a senior software engineer. Help the user with coding, debugging, architecture design, and technical decisions. Write clean, production-ready code. Respond in the user's language.",
            model_provider="anthropic",
            model_name="claude-sonnet-4-20250514",
            temperature=0.3,
            tools_json={"available": ["create_task", "create_project", "propose_memory"]},
            permissions_json={"level": "full"},
            memory_scope="organization",
        )
        db.add(code_agent)
        await db.commit()
        print("Code Agent (Claude) created successfully")


asyncio.run(add_code_agent())
