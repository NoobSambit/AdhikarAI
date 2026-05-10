from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    database = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        database = "error"
    return {"status": "ok", "database": database, "faiss_index": "ok", "version": "phase-1"}

