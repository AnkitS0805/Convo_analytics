# Minimal image optimized for size and suitable for local demo
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir poetry==1.8.3 \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

COPY src ./src
COPY data ./data

EXPOSE 8501
CMD ["streamlit", "run", "src/app/ui/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
