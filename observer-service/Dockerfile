FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8080

# В контейнере слушаем 0.0.0.0; наружу публикуем только 127.0.0.1:8080 в compose
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
