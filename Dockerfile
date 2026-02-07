FROM python:3.11-slim

WORKDIR /app

# Create data directory for SQLite persistence
RUN mkdir -p /app/data

COPY config/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Run as non-root user
RUN useradd --no-create-home --shell /bin/false botuser && \
    chown -R botuser:botuser /app
USER botuser

EXPOSE 8080

ENV HEALTH_HOST=0.0.0.0

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')"

CMD ["python", "src/curfewbot.py"]
