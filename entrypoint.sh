#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -x $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

alembic revision --autogenerate -m "Auto Generate...."  || echo ""
alembic upgrade head 

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

celery -A app.tasks.celery_tasks.celery_app beat  --loglevel=debug &

celery -A app.tasks.celery_tasks.celery_app worker  --loglevel=debug 


exec "$@"



