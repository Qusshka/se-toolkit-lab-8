# Multi-stage build for nanobot gateway
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

WORKDIR /app

# Copy root workspace files
COPY pyproject.toml uv.lock ./

# Copy the nanobot project
COPY nanobot/ ./nanobot/

# Copy the mcp directory
COPY mcp/ ./mcp/

# Copy qwen-code-api (needed for workspace resolution)
COPY qwen-code-api/ ./qwen-code-api/

# Copy backend (needed for workspace resolution)
COPY backend/ ./backend/

# Copy nanobot-websocket-channel for webchat installation
COPY nanobot-websocket-channel/ ./nanobot-websocket-channel/

# Install dependencies including the editable MCP package and webchat
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package nanobot --package lms-mcp && \
    uv pip install /app/nanobot-websocket-channel/nanobot-channel-protocol /app/nanobot-websocket-channel/nanobot-webchat

# Production stage
FROM python:3.14-slim-bookworm

# Create nonroot user (same pattern as backend)
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Copy the virtual environment from builder
COPY --from=builder --chown=nonroot:nonroot /app /app

# Copy entrypoint script
COPY nanobot/entrypoint.py /app/nanobot/entrypoint.py

# Copy the nanobot workspace files with proper ownership
COPY --chown=nonroot:nonroot nanobot/ /app/nanobot/

WORKDIR /app

USER nonroot

CMD ["python", "/app/nanobot/entrypoint.py"]
