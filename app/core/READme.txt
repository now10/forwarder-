- ALTERNATIVE START COMMAND for STABILITY -

# In Render start command:
gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120 --keep-alive 5

- FOR RENDER BUILD -

pip install -r requirements.txt && python -m alembic upgrade head

- FOR RENDER START COMMAND -

uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --timeout-keep-alive 30
        OR
gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120
       