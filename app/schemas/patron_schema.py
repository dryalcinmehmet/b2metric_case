from uuid import UUID
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class PatronBase(BaseModel):
    name: str
    email: str


class Patron(PatronBase):
    id: UUID
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class PatronCreate(PatronBase):
    name: str
    email: str


class PatronUpdate(BaseModel):
    name: Optional[str] = None


class PatronsList(BaseModel):
    patrons: List[Patron]


class PatronDetails(BaseModel):
    patron: Patron
