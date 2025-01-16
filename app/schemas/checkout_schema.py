from uuid import UUID
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class CheckoutBase(BaseModel):
    book_id: UUID
    patron_id: UUID
    due_date: datetime


class Checkout(CheckoutBase):
    id: UUID
    book_id: UUID
    patron_id: UUID
    due_date: datetime
    returned: bool

    class Config:
        from_attributes = True


class CheckoutCreate(BaseModel):
    book_id: UUID
    patron_id: UUID
    due_date: datetime


class CheckoutReturn(BaseModel):
    book_id: UUID

    class Config:
        from_attributes = True


class CheckoutUpdate(BaseModel):
    book_id: UUID
    patron_id: UUID
    due_date: datetime

    class Config:
        from_attributes = True


class CheckoutsList(BaseModel):
    checkouts: List[Checkout]


class CheckoutDetails(BaseModel):
    checkout: Checkout
