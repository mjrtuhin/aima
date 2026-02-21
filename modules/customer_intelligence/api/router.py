from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import uuid

from platform.api.database import get_db

router = APIRouter(prefix="/modules/customer-intelligence")


class SegmentationRequest(BaseModel):
    connector_id: uuid.UUID
    n_segments: str = "auto"
    recompute_features: bool = True


class SegmentationResponse(BaseModel):
    job_id: str
    status: str
    message: str


@router.post("/segment", response_model=SegmentationResponse)
async def trigger_segmentation(
    org_id: uuid.UUID,
    request: SegmentationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    from platform.workers.tasks.inference import train_customer_intelligence_model
    job = train_customer_intelligence_model.delay(
        org_id=str(org_id),
        config={"n_segments": request.n_segments, "connector_id": str(request.connector_id)},
    )
    return SegmentationResponse(
        job_id=job.id,
        status="queued",
        message="Segmentation job queued. Results will be available shortly.",
    )


@router.get("/segments")
async def list_segments(org_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from platform.api.models import CustomerSegment
    result = await db.execute(
        select(CustomerSegment)
        .where(CustomerSegment.org_id == org_id, CustomerSegment.status == "active")
        .order_by(CustomerSegment.customer_count.desc())
    )
    segments = result.scalars().all()
    return segments


@router.get("/customers/{customer_id}/profile")
async def get_customer_profile(
    customer_id: uuid.UUID,
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from platform.api.models import Customer, CustomerFeatures, CustomerSegmentMembership
    customer = (await db.execute(
        select(Customer).where(Customer.id == customer_id, Customer.org_id == org_id)
    )).scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    features = (await db.execute(
        select(CustomerFeatures)
        .where(CustomerFeatures.customer_id == customer_id)
        .order_by(CustomerFeatures.computed_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    return {
        "customer": {
            "id": str(customer.id),
            "email": customer.email,
            "full_name": customer.full_name,
        },
        "features": features.__dict__ if features else None,
    }
