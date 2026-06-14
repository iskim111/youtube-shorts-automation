import json

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.models.enums import UserRole
from app.services.audit_service import list_audit_logs

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: str
    actor_email: str | None
    action: str
    entity_type: str
    entity_id: str
    payload: dict | None
    created_at: str


@router.get("/logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    entity_type: str | None = None,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role(UserRole.AUDITOR, UserRole.ADMIN, UserRole.OPERATOR)),
):
    logs = await list_audit_logs(db, entity_type=entity_type, limit=limit)
    return [
        AuditLogResponse(
            id=str(log.id),
            actor_email=log.actor_email,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            payload=json.loads(log.payload) if log.payload else None,
            created_at=log.created_at.isoformat() if log.created_at else "",
        )
        for log in logs
    ]
