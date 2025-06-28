# cron/Dockerfile
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /code

# Install cron and pip dependencies
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y cron && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy Django project
COPY . .

# Copy cron job definition
COPY cron/crontab /etc/cron.d/redis-cron

# Set correct permissions and register cron job
RUN chmod 0644 /etc/cron.d/redis-cron && \
    crontab /etc/cron.d/redis-cron && \
    touch /var/log/cron.log

# Run cron daemon in foreground
CMD ["cron", "-f"]
