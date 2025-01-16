from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
from fastapi import File, UploadFile


class BookBase(BaseModel):
    title: str
    author: str
    available: bool


class Book(BookBase):
    id: UUID
    title: str
    author: str
    available: bool

    class Config:
        from_attributes = True


class BookCreate(BookBase):
    title: str
    author: str
    available: bool


class BookUpload(BaseModel):
    files: List[UploadFile] = File(
        ..., description="List of image files to upload (only image files accepted)"
    )


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    available: Optional[bool] = None


class BooksList(BaseModel):
    books: List[Book]


class BookDetails(BaseModel):
    book: Book


class CheckedOutBookSchema(BaseModel):
    book_id: UUID
    title: str
    checked_out_by: str
    patron_email: str
    checkout_date: datetime

    class Config:
        from_attributes = True


class OverdueBookSchema(BaseModel):
    book_id: UUID
    title: str
    checked_out_by: str
    patron_email: str
    checkout_date: datetime
    due_date: datetime

    class Config:
        from_attributes = True


class BookOut(BaseModel):
    id: UUID
    title: str
    author: str
    available: bool
