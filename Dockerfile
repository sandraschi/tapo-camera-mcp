FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# System deps (OpenCV needs libGL and other graphics libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-docker.txt /app/requirements-docker.txt

# Install ONLY minimal requirements (excludes ML deps and dev tools)
# Skip 'pip install .' to avoid pulling in extra deps from pyproject.toml
RUN python -m pip install --upgrade pip \
 && pip install -r requirements-docker.txt

COPY . /app

EXPOSE 7777

HEALTHCHECK --interval=30s --timeout=5s --retries=10 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7777/api/health', timeout=4)" || exit 1

ENTRYPOINT ["python", "-m", "tapo_camera_mcp.web.server"]


