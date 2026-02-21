from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import uuid

from platform.api.database import get_db
from platform.api.models import Connector, ConnectorType

router = APIRouter(prefix="/connectors")


class ConnectorCreate(BaseModel):
    type: ConnectorType
    name: str
    config: dict = {}


class ConnectorResponse(BaseModel):
    id: uuid.UUID
    type: str
    name: str
    is_active: bool
    last_synced_at: Optional[str] = None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[ConnectorResponse])
async def list_connectors(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Connector).where(Connector.org_id == org_id, Connector.is_active == True)
    )
    return result.scalars().all()


@router.post("", response_model=ConnectorResponse, status_code=status.HTTP_201_CREATED)
async def create_connector(
    org_id: uuid.UUID,
    payload: ConnectorCreate,
    db: AsyncSession = Depends(get_db),
):
    connector = Connector(org_id=org_id, **payload.model_dump())
    db.add(connector)
    await db.flush()
    return connector


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connector(
    connector_id: uuid.UUID,
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Connector).where(Connector.id == connector_id, Connector.org_id == org_id)
    )
    connector = result.scalar_one_or_none()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    connector.is_active = False
