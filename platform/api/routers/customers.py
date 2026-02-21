from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

from platform.api.database import get_db
from platform.api.models import Customer, CustomerFeatures

router = APIRouter(prefix="/customers")


class CustomerResponse(BaseModel):
    id: uuid.UUID
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    country: Optional[str]
    customer_health_score: Optional[float] = None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[CustomerResponse])
async def list_customers(
    org_id: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Customer).where(Customer.org_id == org_id)
    if search:
        query = query.where(Customer.email.ilike(f"%{search}%"))
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: uuid.UUID,
    org_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Customer).where(Customer.id == customer_id, Customer.org_id == org_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/{customer_id}/features")
async def get_customer_features(
    customer_id: uuid.UUID,
    org_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CustomerFeatures)
        .where(CustomerFeatures.customer_id == customer_id, CustomerFeatures.org_id == org_id)
        .order_by(CustomerFeatures.computed_at.desc())
        .limit(1)
    )
    features = result.scalar_one_or_none()
    if not features:
        raise HTTPException(status_code=404, detail="Features not yet computed for this customer")
    return features
