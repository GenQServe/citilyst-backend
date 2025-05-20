import logging
from typing import List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.village import Village
from schemas.district import VillageCreate, VillageUpdate


class VillageService:
    async def create_village(self, db: AsyncSession, village: VillageCreate) -> dict:
        try:
            village_model = Village(name=village.name, district_id=village.district_id)
            db.add(village_model)
            await db.commit()
            await db.refresh(village_model)
            village = village_model.to_dict()

            return village
        except Exception as e:
            logging.error(f"Error creating village: {str(e)}")
            raise Exception(f"Failed to create village: {str(e)}")

    # get village by district id
    async def get_village_by_district_id(
        self, db: AsyncSession, district_id: str
    ) -> List[dict]:
        try:
            result = await db.execute(
                select(Village).where(Village.district_id == district_id)
            )
            villages = result.scalars().all()
            if not villages:
                raise HTTPException(
                    status_code=404, detail="No villages found for this district"
                )
            return [village.to_dict() for village in villages]
        except HTTPException as e:
            logging.warning(
                f"HTTP error in get_village_by_district_id: {e.status_code} - {e.detail}"
            )
            raise e
        except Exception as e:
            logging.error(f"Error fetching villages by district id: {str(e)}")
            raise Exception(f"Failed to fetch villages by district id: {str(e)}")

    async def get_village_by_id(self, db: AsyncSession, village_id: str) -> dict:
        try:
            result = await db.execute(select(Village).where(Village.id == village_id))
            village_model = result.scalars().first()
            if not village_model:
                raise HTTPException(status_code=404, detail="Village not found")
            return village_model.to_dict()
        except HTTPException as e:
            logging.warning(
                f"HTTP error in get_village_by_id: {e.status_code} - {e.detail}"
            )
            raise e
        except Exception as e:
            logging.error(f"Error fetching village: {str(e)}")
            raise Exception(f"Failed to fetch village: {str(e)}")

    async def get_village_by_name(self, db: AsyncSession, name: str) -> dict:
        try:
            result = await db.execute(select(Village).where(Village.name == name))
            village_model = result.scalars().first()
            if not village_model:
                raise HTTPException(status_code=404, detail="Village not found")
            return village_model.to_dict()
        except HTTPException as e:
            logging.warning(
                f"HTTP error in get_village_by_name: {e.status_code} - {e.detail}"
            )
            raise e
        except Exception as e:
            logging.error(f"Error fetching village: {str(e)}")
            raise Exception(f"Failed to fetch village: {str(e)}")

    async def get_all_villages(self, db: AsyncSession) -> List[dict]:
        try:
            result = await db.execute(select(Village))
            villages = result.scalars().all()
            return [village.to_dict() for village in villages]
        except Exception as e:
            logging.error(f"Error fetching villages: {str(e)}")
            raise Exception(f"Failed to fetch villages: {str(e)}")

    async def delete_village(self, db: AsyncSession, village_id: str) -> dict:
        try:
            result = await db.execute(select(Village).where(Village.id == village_id))
            village_model = result.scalars().first()
            if not village_model:
                raise HTTPException(status_code=404, detail="Village not found")
            await db.delete(village_model)
            await db.commit()
            return village_model.to_dict()
        except HTTPException as e:
            logging.warning(
                f"HTTP error in delete_village: {e.status_code} - {e.detail}"
            )
            raise e
        except Exception as e:
            logging.error(f"Error deleting village: {str(e)}")
            raise Exception(f"Failed to delete village: {str(e)}")

    async def update_village(
        self, db: AsyncSession, village_id: str, village: VillageUpdate
    ) -> dict:
        try:
            result = await db.execute(select(Village).where(Village.id == village_id))
            village_model = result.scalars().first()
            if not village_model:
                raise HTTPException(status_code=404, detail="Village not found")
            for key, value in village.dict(exclude_unset=True).items():
                setattr(village_model, key, value)
            await db.commit()
            await db.refresh(village_model)
            return village_model.to_dict()
        except Exception as e:
            logging.error(f"Error updating village: {str(e)}")
            raise Exception(f"Failed to update village: {str(e)}")
