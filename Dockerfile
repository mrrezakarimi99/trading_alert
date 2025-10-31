# =============================================================================
# DOCKERFILE - CONTAINERIZED DEPLOYMENT
# =============================================================================
# Build: docker build -t crypto-trading:latest .
# Run:   docker run -d --name crypto-trading --restart unless-stopped crypto-trading:latest
# Logs:  docker logs -f crypto-trading
# =============================================================================

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories and set permissions as root
RUN mkdir -p data/csv data/database logs \
    && chmod -R 777 data logs \
    && useradd --create-home --shell /bin/bash --uid 1000 trading \
    && chown -R trading:trading /app

# Switch to non-root user
USER trading

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Expose port (if needed for monitoring)
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]