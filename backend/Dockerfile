FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 colony

COPY --chown=colony:colony . .
USER colony
EXPOSE 8000

# Create tables once before starting workers. No database credentials in this image.
CMD ["sh", "-c", "python init_db.py && exec gunicorn --bind 0.0.0.0:8000 --workers 2 --access-logfile - --error-logfile - app:app"]
