FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY app/crawler-api/pyproject.toml app/crawler-api/uv.lock ./
RUN pip install uv && uv sync --frozen

COPY app/crawler-api/ ./

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
