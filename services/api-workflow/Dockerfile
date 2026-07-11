FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY services/api-workflow/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/api-workflow/app ./app
COPY services/api-workflow/migrations ./migrations
COPY services/api-workflow/tests ./tests
COPY packages/test-fixtures ./fixtures
