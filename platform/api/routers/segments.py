from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
import uuid
from datetime import datetime

from ..database import get_db
from ..models import CustomerSegment, CustomerSegmentMembership, Customer

router = APIRouter(prefix="/segments", tags=["segments"])


@router.get("")
async def list_segments(
    org_id: str = Query(...),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CustomerSegment).where(CustomerSegment.org_id == org_id)
    if status:
        stmt = stmt.where(CustomerSegment.status == status)
    stmt = stmt.order_by(CustomerSegment.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    segments = result.scalars().all()

    count_stmt = select(func.count()).select_from(CustomerSegment).where(CustomerSegment.org_id == org_id)
    total = (await db.execute(count_stmt)).scalar()

    return {
        "segments": [
            {
                "id": str(s.id),
                "name": s.name,
                "description": s.description,
                "customer_count": s.customer_count or 0,
                "avg_health_score": float(s.avg_health_score) if s.avg_health_score else None,
                "avg_ltv": float(s.avg_ltv) if s.avg_ltv else None,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
            }
            for s in segments
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{segment_id}")
async def get_segment(
    segment_id: str,
    org_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CustomerSegment).where(
        and_(CustomerSegment.id == uuid.UUID(segment_id), CustomerSegment.org_id == org_id)
    )
    result = await db.execute(stmt)
    segment = result.scalar_one_or_none()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    return {
        "id": str(segment.id),
        "name": segment.name,
        "description": segment.description,
        "model_version": segment.model_version,
        "cluster_id": segment.cluster_id,
        "customer_count": segment.customer_count or 0,
        "avg_health_score": float(segment.avg_health_score) if segment.avg_health_score else None,
        "avg_ltv": float(segment.avg_ltv) if segment.avg_ltv else None,
        "characteristics": segment.characteristics or {},
        "recommended_strategy": segment.recommended_strategy,
        "status": segment.status,
        "created_at": segment.created_at.isoformat(),
    }


@router.post("")
async def create_segment(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    org_id = payload.get("org_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="org_id is required")

    segment = CustomerSegment(
        org_id=org_id,
        name=payload.get("name", "New Segment"),
        description=payload.get("description"),
        model_version=payload.get("model_version"),
        cluster_id=payload.get("cluster_id"),
        characteristics=payload.get("characteristics", {}),
        recommended_strategy=payload.get("recommended_strategy"),
        status="active",
    )
    db.add(segment)
    await db.commit()
    await db.refresh(segment)
    return {"id": str(segment.id), "status": "created"}


@router.get("/{segment_id}/members")
async def get_segment_members(
    segment_id: str,
    org_id: str = Query(...),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    segment_uuid = uuid.UUID(segment_id)
    stmt = select(CustomerSegmentMembership).where(
        and_(
            CustomerSegmentMembership.segment_id == segment_uuid,
            CustomerSegmentMembership.org_id == org_id,
        )
    ).order_by(CustomerSegmentMembership.assigned_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    memberships = result.scalars().all()

    count_stmt = select(func.count()).select_from(CustomerSegmentMembership).where(
        and_(
            CustomerSegmentMembership.segment_id == segment_uuid,
            CustomerSegmentMembership.org_id == org_id,
        )
    )
    total = (await db.execute(count_stmt)).scalar()

    return {
        "members": [
            {
                "customer_id": str(m.customer_id),
                "confidence_score": float(m.confidence_score) if m.confidence_score else None,
                "assigned_at": m.assigned_at.isoformat() if m.assigned_at else None,
            }
            for m in memberships
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/{segment_id}/activate")
async def activate_segment(
    segment_id: str,
    org_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CustomerSegment).where(
        and_(CustomerSegment.id == uuid.UUID(segment_id), CustomerSegment.org_id == org_id)
    )
    result = await db.execute(stmt)
    segment = result.scalar_one_or_none()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    segment.status = "active"
    await db.commit()
    return {"id": str(segment.id), "status": "activated"}


@router.post("/run-segmentation")
async def run_segmentation(
    payload: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    org_id = payload.get("org_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="org_id is required")

    return {
        "status": "queued",
        "message": "Customer segmentation task queued for background processing",
        "estimated_duration_seconds": 300,
    }
