FROM python:3.12-slim@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr poppler-utils && rm -rf /var/lib/apt/lists/*
COPY services/api-workflow/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/api-workflow/app ./app
COPY services/api-workflow/migrations ./migrations
COPY services/api-workflow/tests ./tests
COPY packages/test-fixtures ./fixtures
