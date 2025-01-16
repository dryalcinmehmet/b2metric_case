import os

import uuid
from app.models.user import User
from app.core.database import DBSessionDep
from app.models.book_model import BookModel
from typing import Annotated, Any, Optional
from app.models.patron_model import PatronModel
from fastapi.security import OAuth2PasswordBearer
from app.models.checkout_model import CheckoutModel
from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status

from app.schemas.checkout_schema import (
    Checkout as CheckoutSchema,
    CheckoutCreate,
    CheckoutDetails,
    CheckoutsList,
    CheckoutUpdate,
    CheckoutReturn,
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
    prefix="/api/checkout",
    tags=["checkouts"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=CheckoutsList)
async def checkout_list(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
):
    payload = await decode_access_token(token=token, db=db)
    checkouts = await CheckoutModel.find_all(db=db)
    return CheckoutsList(checkouts=checkouts)


@router.get("/{id}", response_model=CheckoutDetails)
async def checkout_details(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
    id: str = Path(..., title="The ID of the checkout to delete"),
):
    payload = await decode_access_token(token=token, db=db)
    user = await User.find_by_username(db=db, username=payload.username)

    if not user:
        raise AuthFailedException()
    try:
        uuid_obj = uuid.UUID(id)
    except ValueError:
        raise BadRequestException

    checkout = await CheckoutModel.find_by_id(db=db, id=uuid_obj)
    if checkout is None:
        raise NotFoundException()

    titles = await CheckoutModel.find_by_id(db=db, id=checkout.id)

    checkout_schema = CheckoutSchema.model_validate(checkout.__dict__)
    checkout_details = CheckoutDetails(checkout=checkout_schema, checkout_titles=titles)
    return checkout_details


@router.post("/create/", response_model=CheckoutSchema)
async def create_book(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
    data: CheckoutCreate,
):
    payload = await decode_access_token(token=token, db=db)
    user = await User.find_by_username(db=db, username=payload.username)
    if not user:
        raise AuthFailedException()

    is_book_available = await BookModel.is_available(db=db, id=data.book_id)
    if not is_book_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book has already checked out.",
        )

    patron_model = await PatronModel.find_by_id(db=db, id=data.patron_id)
    if not patron_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No patron found!",
        )

    updated_rows = await BookModel.mark_unavailable(db=db, id=data.book_id)
    if updated_rows == 0:
        raise HTTPException(status_code=404, detail="Book not found")

    checkout_data = data.model_dump()
    checkout = CheckoutModel(**checkout_data)
    checkout = await checkout.create(db=db, **checkout_data)

    checkout_schema = CheckoutSchema.model_validate(checkout.__dict__)
    return checkout_schema


@router.put("/return/{id}", response_model=CheckoutSchema)
async def return_book_checkout(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
    data: CheckoutReturn,
    id: str = Path(..., title="The ID of the checkout to delete"),
):
    payload = await decode_access_token(token=token, db=db)
    user = await User.find_by_username(db=db, username=payload.username)
    if not user:
        raise AuthFailedException()

    try:
        uuid_obj = uuid.UUID(id)
    except ValueError:
        raise BadRequestException

    checkout_model = await CheckoutModel.find_by_id(db=db, id=uuid_obj)
    if checkout_model.book_id != data.book_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wrong book id",
        )

    updated_rows = await BookModel.mark_available(db=db, id=data.book_id)
    if updated_rows == 0:
        raise HTTPException(status_code=404, detail="Book not found")

    updated_checkout = await CheckoutModel.mark_book_return(db=db, id=uuid_obj)

    checkout = await CheckoutModel.find_by_id(db=db, id=uuid_obj)
    if checkout is None:
        raise NotFoundException()

    checkout_schema = CheckoutSchema.model_validate(checkout.__dict__)
    return checkout_schema


@router.delete("/delete/{id}", response_model=None)
async def delete_checkout(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
    id: str = Path(..., title="The ID of the checkout to delete"),
):
    payload = await decode_access_token(token=token, db=db)
    user = await User.find_by_username(db=db, username=payload.username)
    if not user:
        raise AuthFailedException()

    try:
        uuid_obj = uuid.UUID(id)
    except ValueError:
        raise BadRequestException

    checkout = await CheckoutModel.find_by_id(db=db, id=uuid_obj)
    if checkout is None:
        raise NotFoundException()

    # Delete the checkout by its ID
    deleted_checkout = await CheckoutModel.delete(db=db, id=id)
    if not deleted_checkout:
        raise NotFoundException(detail="Checkout not found")

    return {"message": "Checkout deleted successfully"}
