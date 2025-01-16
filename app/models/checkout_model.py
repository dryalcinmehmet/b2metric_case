import uuid
from typing import List, Optional
from . import Base
from app.models.user import User
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from fastapi import APIRouter, Depends, HTTPException, status, Path

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Float,
    DateTime,
    UUID,
    ForeignKey,
    CheckConstraint,
    func,
    select,
    and_,
    delete,
    update,
)


class CheckoutModel(Base):
    __tablename__ = "checkouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    book_id = Column(UUID, ForeignKey("books.id"), nullable=False)
    patron_id = Column(UUID, ForeignKey("patrons.id"), nullable=False)
    checkout_date = Column(DateTime, nullable=False, default=datetime.now())
    returned_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    returned = Column(Boolean, default=False)
    book = relationship("BookModel")
    patron = relationship("PatronModel")

    @classmethod
    async def find_all(cls, db: AsyncSession) -> List["CheckoutModel"]:
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
        new_checkout = cls(**kwargs)
        db.add(new_checkout)
        await db.commit()
        await db.refresh(new_checkout)
        return new_checkout

    @classmethod
    async def mark_book_return(cls, db: AsyncSession, id: UUID):
        stmt = select(cls).filter(cls.id == id)
        result = await db.execute(stmt)
        checkout = result.scalar_one_or_none()

        if checkout is None:
            return None

        checkout.returned = True
        checkout.returned_date = datetime.now()

        db.add(checkout)
        await db.commit()

        await db.refresh(checkout)
        return checkout

    @classmethod
    async def update(cls, db: AsyncSession, id: UUID, **kwargs):
        stmt = select(cls).filter(cls.id == id)
        result = await db.execute(stmt)
        checkout = result.scalar_one_or_none()

        if checkout is None:
            return None

        for key, value in kwargs.items():
            if hasattr(checkout, key):
                setattr(checkout, key, value)

        db.add(checkout)
        await db.commit()
        await db.refresh(checkout)
        return checkout

    @classmethod
    async def delete(cls, db: AsyncSession, id: UUID) -> Optional["CheckoutModel"]:
        stmt = select(cls).where(cls.id == id)
        result = await db.execute(stmt)
        checkout = result.scalars().first()

        if checkout is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Patron not found"
            )

        await db.delete(checkout)
        await db.commit()

        return {"detail": "Patron deleted successfully"}

    @classmethod
    async def check_checkout(cls, db: AsyncSession, status: str, title: str):
        query = select(cls).where(and_(cls.status == status, cls.title == title))
        result = await db.execute(query)
        return result.scalars().first() is None
