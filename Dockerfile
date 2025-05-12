FROM python:3.12-slim

# Set environment variables
ENV DATABASE_URL=""
ENV REDIS_URL="redis://redis:6379"
ENV PYTHONUNBUFFERED=1

# Install dependencies & system packages
RUN apt-get update && apt-get install -y \
    curl \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Set working directory
WORKDIR /app

# Copy file dependencies
COPY requirements.txt .

# Install dependencies
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy seluruh kode aplikasi
COPY . /app/

# Expose port untuk FastAPI
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
