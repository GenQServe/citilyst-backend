import dis
import logging
import os
import secrets
from urllib.parse import urlencode
import redis.asyncio as redis
import requests
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException
from typing import List, Optional
from models.users import User
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from sqlalchemy.future import select
from helpers.redis import set_redis_value, get_redis_value, delete_redis_value
from schemas.district import (
    DistrictCreate,
    DistrictUpdate,
    DistrictResponse,
    DistrictListResponse,
)
from models.district import District


class DistrictService:
    async def create_district(self, db: AsyncSession, district: DistrictCreate) -> dict:
        try:
            district_model = District(name=district.name)
            db.add(district_model)
            await db.commit()
            await db.refresh(district_model)
            district = district_model.to_dict()
            return district
        except Exception as e:
            logging.error(f"Error creating district: {str(e)}")
            raise Exception(f"Failed to create district: {str(e)}")

    async def get_district_by_id(self, db: AsyncSession, district_id: str) -> dict:
        try:
            result = await db.execute(
                select(District).where(District.id == district_id)
            )
            district_model = result.scalars().first()
            if not district_model:
                raise HTTPException(status_code=404, detail="District not found")
            return district_model.to_dict()
        except HTTPException as e:
            logging.warning(
                f"HTTP error in get_district_by_id: {e.status_code} - {e.detail}"
            )
            raise e
        except Exception as e:
            logging.error(f"Error fetching district: {str(e)}")
            raise Exception(f"Failed to fetch district: {str(e)}")

    async def get_district_by_name(self, db: AsyncSession, name: str) -> dict:
        try:
            result = await db.execute(select(District).where(District.name == name))
            district_model = result.scalars().first()
            if not district_model:
                raise HTTPException(status_code=404, detail="District not found")
            return district_model.to_dict()
        except HTTPException as e:
            logging.warning(
                f"HTTP error in get_district_by_name: {e.status_code} - {e.detail}"
            )
            raise e
        except Exception as e:
            logging.error(f"Error fetching district: {str(e)}")
            raise Exception(f"Failed to fetch district: {str(e)}")

    async def get_all_districts(self, db: AsyncSession) -> List[dict]:
        try:
            result = await db.execute(select(District))
            districts = result.scalars().all()
            return [district.to_dict() for district in districts]
        except Exception as e:
            logging.error(f"Error fetching districts: {str(e)}")
            raise Exception(f"Failed to fetch districts: {str(e)}")

    async def delete_district(self, db: AsyncSession, district_id: str) -> dict:
        try:
            result = await db.execute(
                select(District).where(District.id == district_id)
            )
            district_model = result.scalars().first()
            if not district_model:
                raise HTTPException(status_code=404, detail="District not found")
            await db.delete(district_model)
            await db.commit()
            return district_model.to_dict()
        except HTTPException as e:
            logging.warning(
                f"HTTP error in delete_district: {e.status_code} - {e.detail}"
            )
            raise e
        except Exception as e:
            logging.error(f"Error deleting district: {str(e)}")
            raise Exception(f"Failed to delete district: {str(e)}")

    async def update_district(
        self, db: AsyncSession, district_id: str, district: DistrictUpdate
    ) -> dict:
        try:
            result = await db.execute(
                select(District).where(District.id == district_id)
            )
            district_model = result.scalars().first()
            if not district_model:
                raise HTTPException(status_code=404, detail="District not found")
            for key, value in district.dict(exclude_unset=True).items():
                setattr(district_model, key, value)
            await db.commit()
            await db.refresh(district_model)
            return district_model.to_dict()
        except Exception as e:
            logging.error(f"Error updating district: {str(e)}")
            raise Exception(f"Failed to update district: {str(e)}")
