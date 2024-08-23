FROM ghcr.io/astral-sh/uv as uv

FROM python:3.10-slim
WORKDIR /app
COPY pyproject.toml .
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    uv pip install --system -r pyproject.toml
COPY . .
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    uv pip install --system -e .
