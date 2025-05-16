import logging
import os
import secrets
from urllib.parse import urlencode
import redis.asyncio as redis  # Make sure this is the async version
import requests
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException
from helpers.common import hash_password
from helpers.google_auth import GoogleAuth
from typing import List, Optional
from models.users import User
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from sqlalchemy.future import select
from helpers.redis import set_redis_value, get_redis_value, delete_redis_value
from models.feedback_user import FeedbackUser
from schemas.feedback_user import FeedbackUserRequest
from schemas.users import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class FeedbackUserService:
    async def create_feedback_user(
        self, db: AsyncSession, feedback_user: FeedbackUserRequest
    ) -> dict:
        try:
            feedback_user_model = FeedbackUser(
                user_name=feedback_user.user_name,
                user_email=feedback_user.user_email,
                user_image_url=feedback_user.user_image_url,
                description=feedback_user.description,
                location=feedback_user.location,
            )
            db.add(feedback_user_model)
            await db.commit()
            await db.refresh(feedback_user_model)
            feedback_user = feedback_user_model.to_dict()
            return feedback_user
        except Exception as e:
            logging.error(f"Error creating feedback user: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create feedback user: {str(e)}"
            )

    # get all feedback user
    async def get_all_feedback_user(self, db: AsyncSession) -> List[dict]:
        try:
            result = await db.execute(select(FeedbackUser))
            feedback_users = result.scalars().all()
            feedback_users_list = [
                feedback_user.to_dict() for feedback_user in feedback_users
            ]
            return feedback_users_list
        except Exception as e:
            logging.error(f"Error getting all feedback users: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get all feedback users: {str(e)}"
            )
