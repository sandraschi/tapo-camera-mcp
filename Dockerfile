FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (add cv/ffmpeg libs later if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* requirements.txt* /app/

# Prefer pip with pyproject; fallback to requirements if present
RUN python -m pip install --upgrade pip \
 && ( [ -f requirements.txt ] && pip install -r requirements.txt || true ) \
 && pip install .

COPY . /app

EXPOSE 7777

HEALTHCHECK --interval=30s --timeout=5s --retries=10 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7777/api/health', timeout=4)" || exit 1

ENTRYPOINT ["python", "-m", "tapo_camera_mcp.web.server"]


