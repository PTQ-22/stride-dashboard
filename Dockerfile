# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8050

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and install the package.
COPY src ./src
COPY assets ./assets
COPY data ./data
COPY wsgi.py ./
RUN pip install --no-cache-dir -e .

EXPOSE 8050

# Run as non-root for safety.
RUN useradd -m runner && chown -R runner /app
USER runner

CMD ["gunicorn", "wsgi:server", "--bind", "0.0.0.0:8050", "--workers", "2", "--timeout", "120"]
