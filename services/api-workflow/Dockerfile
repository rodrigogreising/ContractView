FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr poppler-utils && rm -rf /var/lib/apt/lists/*
COPY services/api-workflow/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/api-workflow/app ./app
COPY services/api-workflow/migrations ./migrations
COPY services/api-workflow/tests ./tests
COPY packages/test-fixtures ./fixtures
