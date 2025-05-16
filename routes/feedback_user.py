import logging
import os
import sys
from typing import Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.params import Cookie, Header
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from helpers.common import create_verification_token
from helpers.google_auth import GoogleAuth
from sqlalchemy.ext.asyncio import AsyncSession
from helpers.db import db_connection, get_db
from helpers.jwt import JwtHelper
from middleware.rbac_middleware import verify_role
from schemas.users import UserCreate
from services.auth import AuthService
import redis.asyncio as redis
from helpers.config import settings
from services.feedback_user import FeedbackUserService
from schemas.feedback_user import FeedbackUserRequest
from helpers.redis import get_redis_value, set_redis_value, delete_redis_value

from services.users import UserService


routes_feedback_user = APIRouter(prefix="/feedback-user", tags=["Feedback User"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@routes_feedback_user.post(
    "/",
    response_model=dict,
    summary="Create feedback user",
)
async def create_feedback_user(
    feedback_user: FeedbackUserRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create feedback user
    """
    try:
        feedback_user_service = FeedbackUserService()
        feedback_user = await feedback_user_service.create_feedback_user(
            db, feedback_user
        )
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Feedback user created successfully",
                "data": jsonable_encoder(feedback_user),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})


# buatkan route untuk get all feedback user
@routes_feedback_user.get(
    "/",
    response_model=dict,
    summary="Get all feedback user",
)
async def get_all_feedback_user(
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get all feedback user
    """
    try:
        feedback_user_service = FeedbackUserService()
        feedback_user = await feedback_user_service.get_all_feedback_user(db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Feedback user retrieved successfully",
                "data": jsonable_encoder(feedback_user),
            },
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
