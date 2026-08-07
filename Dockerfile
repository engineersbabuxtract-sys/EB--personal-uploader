# Dockerfile.koyeb
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    aria2 \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/downloads /app/cookies /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV WEBHOOK=false
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application
CMD ["bash", "start-koyeb.sh"]
