FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY moneybot ./moneybot

# The ledger lives on a mounted volume, not in the image.
ENV MONEYBOT_DB=/data/moneybot.db MONEYBOT_MEDIA_DIR=/data/media PORT=8080
VOLUME ["/data"]
EXPOSE 8080

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 1 --timeout 120 moneybot.app:app"]
