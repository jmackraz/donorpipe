FROM python:3.13-slim AS builder
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
RUN uv sync --no-dev --no-editable

FROM python:3.13-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "donorpipe.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
