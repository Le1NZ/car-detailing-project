# User Service Dockerfile
# Manages user authentication and profiles with PostgreSQL + Alembic migrations

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose service port
EXPOSE 8001

# Run Alembic migrations then start the application
# This ensures database schema is up-to-date before service starts
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8001"]
