FROM python:3.11-slim-bullseye AS release

ENV WORKSPACE_ROOT=/app/
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV UV_LINK_MODE=copy

# Install Google Chrome
RUN apt-get update -y && \
    apt-get install -y gnupg wget curl --no-install-recommends && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-linux-signing-key.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/google-linux-signing-key.gpg] https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update -y && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Install other system dependencies.
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends build-essential \
    gcc \
    python3-dev \
    build-essential \
    libglib2.0-dev \
    libnss3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv (static binary from the official image).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR $WORKSPACE_ROOT

# Copy the lock file and pyproject.toml first to leverage layer caching.
COPY pyproject.toml uv.lock $WORKSPACE_ROOT

# Install dependencies into the project venv: main + aws groups, without dev.
RUN uv sync --frozen --no-default-groups --group aws

# Put the project venv on PATH so python/poe/uvicorn resolve without `uv run`.
ENV PATH="/app/.venv/bin:$PATH"

# Copy the rest of the code.
COPY . $WORKSPACE_ROOT
