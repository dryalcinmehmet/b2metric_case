from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Float,
    DateTime,
    Date,
    UUID,
    ForeignKey,
    CheckConstraint,
    func,
    select,
    and_,
    delete,
    update,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from . import Base
from app.models.user import User
import uuid
from fastapi import HTTPException, status
from fastapi import APIRouter, Depends, HTTPException, status, Path

from datetime import datetime


class PatronModel(Base):
    __tablename__ = "patrons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now())

    @classmethod
    async def find_all(cls, db: AsyncSession) -> List["PatronModel"]:
        query = select(cls)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def find_by_id(cls, db: AsyncSession, id: UUID):
        query = select(cls).where(cls.id == id)
        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def create(cls, db: AsyncSession, **kwargs):
        new_patron = cls(**kwargs)
        db.add(new_patron)
        await db.commit()
        await db.refresh(new_patron)
        return new_patron

    @classmethod
    async def update(cls, db: AsyncSession, id: UUID, **kwargs):
        stmt = select(cls).filter(cls.id == id)
        result = await db.execute(stmt)
        patron = result.scalar_one_or_none()

        if patron is None:
            return None

        for key, value in kwargs.items():
            if hasattr(patron, key):
                setattr(patron, key, value)

        db.add(patron)
        await db.commit()
        await db.refresh(patron)
        return patron

    @classmethod
    async def delete(cls, db: AsyncSession, id: UUID) -> Optional["PatronModel"]:
        stmt = select(cls).where(cls.id == id)
        result = await db.execute(stmt)
        patron = result.scalars().first()

        if patron is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Patron not found"
            )

        await db.delete(patron)
        await db.commit()

        return {"detail": "Patron deleted successfully"}

    @classmethod
    async def check_patron(cls, db: AsyncSession, email: str):
        query = select(cls).where(and_(cls.email == email))
        result = await db.execute(query)
        return result.scalars().first() is None
