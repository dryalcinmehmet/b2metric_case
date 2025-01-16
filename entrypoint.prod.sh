#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

alembic revision --autogenerate -m "Auto Generate..."  || echo ""
alembic upgrade head 

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

celery -A app.tasks.celery_tasks.celery_app beat
celery -A app.tasks.celery_tasks.celery_app worker


exec "$@"