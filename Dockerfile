FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt pyproject.toml README.md ./
COPY assistant ./assistant
COPY examples ./examples
COPY web ./web
COPY reports ./reports
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir -e .
EXPOSE 8000
CMD ["uvicorn", "assistant.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

