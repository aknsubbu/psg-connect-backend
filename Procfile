web: gunicorn -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --worker-tmp-dir /dev/shm server:app
