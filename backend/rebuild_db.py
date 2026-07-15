import asyncio
from app.core.database import engine, Base
from app.models import *

async def rebuild():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("All tables recreated successfully")

asyncio.run(rebuild())
