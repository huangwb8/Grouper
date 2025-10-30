FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

COPY . ./

ENV GROUPER_WEB_HOST=0.0.0.0
ENV GROUPER_WEB_PORT=8000
ENV GROUPER_EXPORT_DIR=/app/exports

EXPOSE 8000

CMD ["python", "-m", "grouper.web_app"]
