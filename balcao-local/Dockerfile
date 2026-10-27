FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
COPY kb/ ./kb/

RUN useradd -m app && chown -R app:app /app
USER app

RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src"

EXPOSE 8091

CMD ["uvicorn", "balcao.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8091"]
