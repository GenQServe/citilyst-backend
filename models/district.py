from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, ARRAY, func
from sqlalchemy.orm import relationship
from helpers.common import generate_cuid
from helpers.db import Base


class District(Base):
    __tablename__ = "tbl_district"

    id = Column(String(25), primary_key=True, default=generate_cuid)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    villages = relationship(
        "Village", back_populates="district", cascade="all, delete-orphan"
    )
    reports = relationship("Report", back_populates="district")

    def __init__(self, name: str):
        self.name = name
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_dict_with_villages(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "villages": (
                [village.to_dict() for village in self.villages]
                if self.villages
                else []
            ),
        }
