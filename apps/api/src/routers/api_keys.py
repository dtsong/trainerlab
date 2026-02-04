"""API key management endpoints for content creators."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.dependencies import CreatorUser
from src.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyListResponse,
    ApiKeyResponse,
)
from src.services.api_key_service import ApiKeyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CreatorUser,
    key_data: ApiKeyCreate,
) -> ApiKeyCreatedResponse:
    """Create a new API key.

    Requires creator access. The full key is only returned once on creation.
    Store it securely - it cannot be retrieved again.
    """
    service = ApiKeyService(db)
    api_key, full_key = await service.create_api_key(
        user=current_user,
        name=key_data.name,
        monthly_limit=key_data.monthly_limit,
    )
    return ApiKeyCreatedResponse(
        api_key=ApiKeyResponse.model_validate(api_key),
        full_key=full_key,
    )


@router.get("")
async def list_api_keys(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CreatorUser,
) -> ApiKeyListResponse:
    """List API keys for the current creator.

    Requires creator access.
    """
    service = ApiKeyService(db)
    api_keys = await service.list_user_api_keys(current_user)
    return ApiKeyListResponse(
        items=[ApiKeyResponse.model_validate(k) for k in api_keys],
        total=len(api_keys),
    )


@router.get("/{key_id}")
async def get_api_key(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CreatorUser,
    key_id: UUID,
) -> ApiKeyResponse:
    """Get an API key by ID.

    Requires creator access and ownership.
    """
    service = ApiKeyService(db)
    api_key = await service.get_api_key(key_id, current_user)
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )
    return ApiKeyResponse.model_validate(api_key)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CreatorUser,
    key_id: UUID,
) -> None:
    """Revoke an API key.

    Requires creator access and ownership. This action cannot be undone.
    """
    service = ApiKeyService(db)
    revoked = await service.revoke_api_key(key_id, current_user)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )
