import os
import uuid
from typing import List
from app.models.user import User
from app.core.database import DBSessionDep
from app.models.book_model import BookModel
from typing import Annotated, Any, Optional
from app.models.book_model import BookModel
from app.schemas.book_schema import BookUpdate
from fastapi.security import OAuth2PasswordBearer
from app.tasks.celery_tasks import send_overdue_reminders
from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status

from app.schemas.book_schema import (
    Book as BookSchema,
    BookCreate,
    BookDetails,
    BooksList,
    CheckedOutBookSchema,
    BookOut,
    OverdueBookSchema,
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
    prefix="/api/book",
    tags=["books"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=BooksList)
async def book_list(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
):
    payload = await decode_access_token(token=token, db=db)
    books = await BookModel.find_all(db=db)
    return BooksList(books=books)


@router.get("/{id}", response_model=BookDetails)
async def book_details(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
    id: str = Path(..., title="The ID of the book to delete"),
):
    payload = await decode_access_token(token=token, db=db)
    user = await User.find_by_username(db=db, username=payload.username)

    if not user:
        raise AuthFailedException()
    try:
        uuid_obj = uuid.UUID(id)
    except ValueError:
        raise BadRequestException

    book = await BookModel.find_by_id(db=db, id=uuid_obj)
    if book is None:
        raise NotFoundException()

    book = await BookModel.find_by_id(db=db, id=book.id)

    book_schema = BookSchema.model_validate(book.__dict__)
    book_details = BookDetails(book=book_schema, book_titles=book)
    return book_details


@router.post("/create/", response_model=BookSchema)
async def create_book(
    token: Annotated[str, Depends(oauth2_scheme)], db: DBSessionDep, data: BookCreate
):
    payload = await decode_access_token(token=token, db=db)
    user = await User.find_by_username(db=db, username=payload.username)
    if not user:
        raise AuthFailedException()

    if not await BookModel.check_book(db=db, author=data.author, title=data.title):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book title already exists for the user",
        )

    book_data = data.model_dump()

    book = BookModel(**book_data)

    book = await book.create(db=db, **book_data)

    book_schema = BookSchema.model_validate(book.__dict__)
    return book_schema


@router.put("/update/{id}", response_model=None)
async def update_book(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
    id: str,
    data: BookUpdate,
):
    payload = await decode_access_token(token=token, db=db)
    user = await User.find_by_username(db=db, username=payload.username)
    if not user:
        raise AuthFailedException()

    try:
        uuid_obj = uuid.UUID(id)
    except ValueError:
        raise BadRequestException

    book = await BookModel.find_by_id(db=db, id=uuid_obj)
    if book is None:
        raise NotFoundException()

    if data.available not in (True, False):
        raise ForbiddenException("Status should be in  (True, False)")

    updated_book = await book.update(db=db, id=id, **data.__dict__)

    return {
        "id": str(updated_book.id),
        "title": updated_book.title,
        "author": updated_book.author,
        "available": updated_book.available,
    }


@router.delete("/delete/{id}", response_model=None)
async def delete_book(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
    id: str = Path(..., title="The ID of the book to delete"),
):
    payload = await decode_access_token(token=token, db=db)
    user = await User.find_by_username(db=db, username=payload.username)
    if not user:
        raise AuthFailedException()

    try:
        uuid_obj = uuid.UUID(id)
    except ValueError:
        raise BadRequestException

    book = await BookModel.find_by_id(db=db, id=uuid_obj)
    if book is None:
        raise NotFoundException()

    deleted_book = await BookModel.delete(db=db, id=id)
    if not deleted_book:
        raise NotFoundException(detail="Book not found")

    return {"message": "Book deleted successfully"}


@router.get("/checked-out/", response_model=List[CheckedOutBookSchema])
async def get_checked_out_books(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
):
    books = await BookModel.checked_out(db=db)
    return [
        {
            "book_id": book["book_id"],
            "title": book["title"],
            "patron_email": book["patron_email"],
            "checked_out_by": book["checked_out_by"],
            "checkout_date": book["checkout_date"],
            "due_date": book["due_date"],
        }
        for book in books
    ]


@router.get("/send-overdue-reminders/", response_model=List[OverdueBookSchema])
async def send_reminders(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
):

    overdue_books = await BookModel.overdue(db)

    books = [
        {
            "book_id": row["book_id"],
            "title": row["title"],
            "checked_out_by": row["checked_out_by"],
            "patron_email": row["patron_email"],
            "checkout_date": row["checkout_date"],
            "due_date": row["due_date"],
        }
        for row in overdue_books
    ]

    send_overdue_reminders.apply_async(args=[books])
    return {"message": "Overdue reminders have been sent!"}


@router.get("/overdue-books/", response_model=List[OverdueBookSchema])
async def get_overdue_books(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
):
    books = await BookModel.overdue(db=db)

    return [
        {
            "book_id": row["book_id"],
            "title": row["title"],
            "checked_out_by": row["checked_out_by"],
            "patron_email": row["patron_email"],
            "checkout_date": row["checkout_date"],
            "due_date": row["due_date"],
        }
        for row in books
    ]


@router.put("/{book_id}/mark-available", response_model=BookOut)
async def mark_book_available(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
    book_id: str = Path(..., title="The ID of the book to update"),
):
    updated_rows = await BookModel.mark_available(db=db, id=book_id)
    if updated_rows == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    book = await BookModel.find_by_id(db=db, id=book_id)

    book_schema = BookSchema.model_validate(book.__dict__)
    book_details = BookDetails(book=book_schema, book_titles=book)
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "available": book.available,  
    }


@router.put("/{book_id}/mark-unavailable", response_model=BookOut)
async def mark_book_unavailable(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
    book_id: str = Path(..., title="The ID of the book to update"),
):
    updated_rows = await BookModel.mark_unavailable(db=db, id=book_id)
    if updated_rows == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    book = await BookModel.find_by_id(db=db, id=book_id)

    book_schema = BookSchema.model_validate(book.__dict__)
    book_details = BookDetails(book=book_schema, book_titles=book)
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "available": book.available,  
    }
