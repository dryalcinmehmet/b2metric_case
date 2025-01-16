import uuid
from . import Base
from datetime import datetime
from app.models.user import User
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.patron_model import PatronModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.checkout_model import CheckoutModel
from app.schemas.book_schema import CheckedOutBookSchema
from sqlalchemy import Column, Integer, String, DateTime, Enum
from fastapi import APIRouter, Depends, HTTPException, status, Path

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

class BookModel(Base):
    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    available = Column(Boolean, default=True)

    @classmethod
    async def find_all(cls, db: AsyncSession) -> List["BookModel"]:
        query = select(cls)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def find_by_id(cls, db: AsyncSession, id: UUID):
        query = select(cls).where(cls.id == id)
        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def checked_out(cls, db: AsyncSession) -> List[CheckedOutBookSchema]:
        query = (
            select(
                CheckoutModel.book_id,
                BookModel.title,
                PatronModel.name.label("checked_out_by"),
                PatronModel.email.label("patron_email"),
                CheckoutModel.checkout_date,
                CheckoutModel.due_date,
            )
            .join(BookModel, CheckoutModel.book_id == BookModel.id)
            .join(PatronModel, CheckoutModel.patron_id == PatronModel.id)
            .filter(CheckoutModel.returned == False)
            .distinct() 
        )
        result = await db.execute(query)
        return result.mappings().all()

    @classmethod
    async def overdue(cls, db: AsyncSession) -> List[CheckedOutBookSchema]:
        query = (
            select(
                CheckoutModel.book_id,
                BookModel.title,
                PatronModel.name.label("checked_out_by"),
                PatronModel.email.label("patron_email"),
                CheckoutModel.checkout_date,
                CheckoutModel.due_date,
            )
            .join(BookModel, CheckoutModel.book_id == BookModel.id)
            .join(PatronModel, CheckoutModel.patron_id == PatronModel.id)
            .filter(CheckoutModel.returned == False)  
            .filter(
                CheckoutModel.due_date < datetime.now()
            ) 
        )

        result = await db.execute(query)
        return result.mappings().all()

    @classmethod
    def overdue_s(cls, db: Session) -> List[CheckedOutBookSchema]:
        query = (
            select(
                CheckoutModel.book_id,
                BookModel.title,
                PatronModel.name.label("checked_out_by"),
                PatronModel.email.label("patron_email"),
                CheckoutModel.checkout_date,
                CheckoutModel.due_date,
            )
            .join(BookModel, CheckoutModel.book_id == BookModel.id)
            .join(PatronModel, CheckoutModel.patron_id == PatronModel.id)
            .filter(CheckoutModel.returned == False) 
            .filter(
                CheckoutModel.due_date < datetime.now()
            )  
        )

        result = db.execute(query) 
        return result

    @classmethod
    async def create(cls, db: AsyncSession, **kwargs):
        new_asset = cls(**kwargs)
        db.add(new_asset)
        await db.commit()
        await db.refresh(new_asset)
        return new_asset

    @classmethod
    async def update(cls, db: AsyncSession, id: UUID, **kwargs):
        stmt = select(cls).filter(cls.id == id)
        result = await db.execute(stmt)
        asset = result.scalar_one_or_none()

        if asset is None:
            return None

        for key, value in kwargs.items():
            if hasattr(asset, key):
                setattr(asset, key, value)

        db.add(asset)
        await db.commit()
        await db.refresh(asset)
        return asset

    @classmethod
    async def delete(cls, db: AsyncSession, id: UUID) -> Optional["BookModel"]:
        stmt = select(cls).where(cls.id == id)
        result = await db.execute(stmt)
        asset = result.scalars().first()

        if asset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
            )

        await db.delete(asset)
        await db.commit()

        return {"detail": "Book deleted successfully"}

    @classmethod
    async def check_book(cls, db: AsyncSession, author: str, title: str):
        query = select(cls).where(and_(cls.author == author, cls.title == title))
        result = await db.execute(query)
        return result.scalars().first() is None

    @classmethod
    async def is_available(cls, db: AsyncSession, id: UUID):
        query = select(cls.available).where(and_(cls.id == id))
        result = await db.execute(query)
        available = result.scalars().first()
        return available

    @classmethod
    async def mark_available(cls, db: AsyncSession, id: UUID):
        query = update(cls).where(cls.id == id).values(available=True)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount

    @classmethod
    async def mark_unavailable(cls, db: AsyncSession, id: UUID):
        query = update(cls).where(cls.id == id).values(available=False)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount
