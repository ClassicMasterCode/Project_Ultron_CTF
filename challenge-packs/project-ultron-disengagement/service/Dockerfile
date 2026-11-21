# HERCULES Secure Challenge Container
# PROJECT ULTRON: DISENGAGEMENT
FROM python:3.12-slim

# Create isolated non-root user
RUN groupadd -g 1337 ultron && \
    useradd -u 1337 -g ultron -m -s /bin/bash ultron

WORKDIR /app

# Copy application files
COPY service/ /app/service/
COPY private/feedback/ /app/private/feedback/

# Set strict permissions
RUN chown -R ultron:ultron /app && \
    chmod -R 750 /app

# Drop all privileges
USER ultron

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')" || exit 1

ENTRYPOINT ["python3", "/app/service/server.py"]
