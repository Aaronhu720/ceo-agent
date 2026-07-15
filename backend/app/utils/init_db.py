"""Database initialization: create default roles and CEO Agent."""
import asyncio
import uuid

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine, Base
from app.models import *  # noqa


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        from app.models.user import Role
        from app.models.agent import Agent

        existing = await db.execute(select(Role).where(Role.name == "owner"))
        if not existing.scalar_one_or_none():
            default_roles = [
                Role(name="owner", description="Organization owner - full access"),
                Role(name="super_admin", description="Super administrator"),
                Role(name="executive", description="Executive level access"),
                Role(name="manager", description="Manager level access"),
                Role(name="operator", description="Operator level access"),
                Role(name="purchaser", description="Purchasing access"),
                Role(name="finance", description="Finance access"),
                Role(name="warehouse", description="Warehouse access"),
                Role(name="designer", description="Designer access"),
                Role(name="viewer", description="Read-only access"),
            ]
            db.add_all(default_roles)
            await db.flush()
            print("Created default roles")

        ceo_check = await db.execute(select(Agent).where(Agent.agent_type == "ceo"))
        if not ceo_check.scalar_one_or_none():
            placeholder_org_id = uuid.uuid4()
            ceo_agent = Agent(
                organization_id=placeholder_org_id,
                name="CEO Agent",
                agent_type="ceo",
                description="Your AI business partner. Helps with decisions, task tracking, memory management, and daily operations.",
                system_instructions="You are CEO Agent, an AI business partner for enterprise founders.",
                model_provider="openai",
                model_name="gpt-4o",
                temperature=0.7,
                tools_json={
                    "available": [
                        "create_task", "update_task", "create_project", "update_project",
                        "create_decision", "propose_memory", "confirm_memory",
                        "search_memory", "search_entities", "search_files",
                        "generate_daily_brief", "generate_daily_review",
                        "create_notification",
                    ]
                },
                permissions_json={"level": "full", "can_create_tasks": True, "can_propose_memories": True},
                memory_scope="organization",
            )
            db.add(ceo_agent)
            print("Created CEO Agent")

        await db.commit()
        print("Database initialized successfully")


def main():
    asyncio.run(init_db())


if __name__ == "__main__":
    main()
