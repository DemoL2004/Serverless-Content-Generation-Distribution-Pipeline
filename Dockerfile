# Use official Python slim image
FROM python:3.11-slim

# Set environment variables to avoid interactive prompts and unnecessary cache
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install ffmpeg and build essentials for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Optional: Set ENV flag for cloud logic in Python
ENV ENV=cloud

# Default command to run the script
CMD ["python", "main.py"]
