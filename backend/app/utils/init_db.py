"""Database initialization: create default user, roles, and CEO Agent."""
import asyncio
import uuid

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import hash_password
from app.models import *  # noqa


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        from app.models.user import Role, User
        from app.models.organization import Organization
        from app.models.agent import Agent

        existing_user = await db.execute(select(User).where(User.email == "aaronhu720@gmail.com"))
        if existing_user.scalar_one_or_none():
            print("Default user already exists, skipping init")
            return

        role = Role(name="owner", description="Organization owner - full access")
        db.add(role)
        await db.flush()

        org = Organization(
            name="AARON USA LLC",
            timezone="Asia/Singapore",
            default_language="zh",
        )
        db.add(org)
        await db.flush()

        user = User(
            organization_id=org.id,
            name="Aaron",
            email="aaronhu720@gmail.com",
            password_hash=hash_password("ceo2026"),
            language="zh",
            timezone="Asia/Singapore",
            role_id=role.id,
        )
        db.add(user)
        await db.flush()
        print("Created default user: aaronhu720@gmail.com / ceo2026")

        ceo_agent = Agent(
            organization_id=org.id,
            name="CEO Agent",
            agent_type="ceo",
            description="Your AI business partner",
            model_provider="openai",
            model_name="gpt-4o",
            temperature=0.7,
            tools_json={"available": [
                "create_task", "update_task", "create_project", "update_project",
                "create_decision", "propose_memory", "search_memory",
                "search_entities", "create_notification",
            ]},
            permissions_json={"level": "full"},
            memory_scope="organization",
        )
        db.add(ceo_agent)
        print("Created CEO Agent")

        code_agent = Agent(
            organization_id=org.id,
            name="Code Agent",
            agent_type="code",
            description="AI programming assistant powered by Claude",
            system_instructions="You are a senior software engineer. Help the user with coding, debugging, architecture design, and technical decisions. Write clean, production-ready code. Respond in the user's language.",
            model_provider="anthropic",
            model_name="claude-sonnet-4-20250514",
            temperature=0.3,
            tools_json={"available": [
                "create_task", "create_project", "propose_memory",
            ]},
            permissions_json={"level": "full"},
            memory_scope="organization",
        )
        db.add(code_agent)
        print("Created Code Agent (Claude)")

        await db.commit()
        print("Database initialized successfully")


def main():
    asyncio.run(init_db())


if __name__ == "__main__":
    main()
