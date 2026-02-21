from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from platform.api.database import get_db

router = APIRouter(prefix="/alerts")


@router.get("")
async def list_alerts(db: AsyncSession = Depends(get_db)):
    return {"module": "alerts", "status": "coming_soon"}
