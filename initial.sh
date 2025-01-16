:wq
:wq

alembic revision --autogenerate -m "Commit db.."
alembic upgrade head

kill -9 $(lsof -t -i:8001) || echo "ok" &&  uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload