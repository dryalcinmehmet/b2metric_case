import os
import uuid
from app.models.user import User
from app.core.database import DBSessionDep
from typing import Annotated, Any, Optional
from app.models.patron_model import PatronModel
from fastapi.security import OAuth2PasswordBearer
from app.schemas.patron_schema import PatronUpdate
from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status


from app.schemas.patron_schema import (
    Patron as PatronSchema,
    PatronCreate,
    PatronDetails,
    PatronsList,
)

from app.core.exceptions import (
    AuthFailedException,
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)

from app.core.jwt import (
    mail_token,
    create_token_pair,
    refresh_token_state,
    decode_access_token,
    add_refresh_token_cookie,
    oauth2_scheme,
    SUB,
    JTI,
    EXP,
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/api/patron",
    tags=["patrons"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=PatronsList)
async def patron_list(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
):
    payload = await decode_access_token(token=token, db=db)
    patrons = await PatronModel.find_all(db=db)
    return PatronsList(patrons=patrons)


@router.get("/{id}", response_model=PatronDetails)
async def patron_details(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
    id: str = Path(..., title="The ID of the patron to delete"),
):
    payload = await decode_access_token(token=token, db=db)
    user = await User.find_by_username(db=db, username=payload.username)

    if not user:
        raise AuthFailedException()
    try:
        uuid_obj = uuid.UUID(id)
    except ValueError:
        raise BadRequestException

    patron = await PatronModel.find_by_id(db=db, id=uuid_obj)
    if patron is None:
        raise NotFoundException()

    titles = await PatronModel.find_by_id(db=db, id=patron.id)

    patron_schema = PatronSchema.model_validate(patron.__dict__)
    patron_details = PatronDetails(patron=patron_schema, patron_titles=titles)
    return patron_details


@router.post("/create/", response_model=PatronSchema)
async def create_patron(
    token: Annotated[str, Depends(oauth2_scheme)], db: DBSessionDep, data: PatronCreate
):
    payload = await decode_access_token(token=token, db=db)
    user = await User.find_by_username(db=db, username=payload.username)
    if not user:
        raise AuthFailedException()

    if not await PatronModel.check_patron(db=db, email=data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patron title already exists for the user",
        )

    patron_data = data.model_dump()
    patron = PatronModel(**patron_data)

    patron = await patron.create(db=db, **patron_data)
    patron_schema = PatronSchema.model_validate(patron.__dict__)
    return patron_schema


@router.put("/update/{id}", response_model=None)
async def update_patron(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
    id: str,
    data: PatronUpdate,
):
    payload = await decode_access_token(token=token, db=db)
    user = await User.find_by_username(db=db, username=payload.username)
    if not user:
        raise AuthFailedException()

    try:
        uuid_obj = uuid.UUID(id)
    except ValueError:
        raise BadRequestException

    patron = await PatronModel.find_by_id(db=db, id=uuid_obj)
    if patron is None:
        raise NotFoundException()

    updated_patron = await patron.update(db=db, id=id, **data.__dict__)

    return {
        "id": str(updated_patron.id),
        "name": updated_patron.name,
    }


@router.delete("/delete/{id}", response_model=None)
async def delete_patron(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
    id: str = Path(..., title="The ID of the patron to delete"),
):
    payload = await decode_access_token(token=token, db=db)
    user = await User.find_by_username(db=db, username=payload.username)
    if not user:
        raise AuthFailedException()

    try:
        uuid_obj = uuid.UUID(id)
    except ValueError:
        raise BadRequestException

    patron = await PatronModel.find_by_id(db=db, id=uuid_obj)
    if patron is None:
        raise NotFoundException()

    deleted_patron = await PatronModel.delete(db=db, id=id)
    if not deleted_patron:
        raise NotFoundException(detail="Patron not found")

    return {"message": "Patron deleted successfully"}
