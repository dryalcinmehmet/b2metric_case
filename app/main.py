import logging
import sys
from contextlib import asynccontextmanager
from celery import Celery

import uvicorn
from app.routers.auth import router as auth_router
from app.routers.book_router import router as book_router
from app.routers.patron_router import router as patron_router
from app.routers.checkout_router import router as checkout_router

from app.core.config import settings
from app.core.database import sessionmanager
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To understand more, read https://fastapi.tiangolo.com/advanced/events/
    """
    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan, title=settings.project_name, docs_url="/api/docs")
origins = [
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def generate_openapi_schema():
    """
    Generate the OpenAPI schema for the FastAPI application.
    """
    return get_openapi(
        title="My API",
        version="1.0.0",
        description="This is my API description",
        routes=app.routes,
    )


@app.get("/openapi.json")
def get_openapi_endpoint():
    """
    Retrieve the generated OpenAPI schema.
    """
    return JSONResponse(content=generate_openapi_schema())


@app.get("/")
async def root():
    return {
        "message": "Async, FasAPI, PostgreSQL, JWT authntication, Alembic migrations Boilerplate"
    }


# Routers
app.include_router(auth_router)
app.include_router(book_router)
app.include_router(checkout_router)
app.include_router(patron_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)
