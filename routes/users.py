from helpers.config import settings
import redis.asyncio as redis
from fastapi import Cookie, HTTPException, Request, Depends, status, APIRouter
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from services.users import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from helpers.redis import (
    get_redis_client,
    set_redis_value,
    get_redis_value,
    delete_redis_value,
)
from helpers.db import get_db
from middleware.rbac_middleware import verify_role

routes_user = APIRouter(prefix="/user", tags=["User"])


@routes_user.get("/{user_id}", response_model=dict, summary="Get user profile by id")
async def get_user_by_id(
    user_id: str,
    token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_role(["admin"])),
) -> JSONResponse:
    """
    Get user profile by id
    """
    try:
        user_service = UserService()
        user = await user_service.get_user(db, user_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "User profile retrieved successfully",
                "data": jsonable_encoder(user),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
