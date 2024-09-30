# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.6
FROM python:${PYTHON_VERSION}-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

USER appuser

COPY . .

# Expose port 8000, but use $PORT if set
EXPOSE 8000

# Use the custom command to run the server, using $PORT if set, otherwise default to 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]