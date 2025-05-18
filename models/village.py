from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, ARRAY, func
from sqlalchemy.orm import relationship
from helpers.common import generate_cuid
from helpers.db import Base


class Village(Base):
    __tablename__ = "tbl_village"

    id = Column(String(25), primary_key=True, default=generate_cuid)
    name = Column(String(255), nullable=False)
    district_id = Column(String(25), ForeignKey("tbl_district.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    district = relationship("District", back_populates="villages")

    def __init__(self, name: str, district_id: str):
        self.name = name
        self.district_id = district_id
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "district_id": self.district_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
