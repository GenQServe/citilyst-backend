FROM python:3.12-slim

# Install dependencies & system packages
RUN apt-get update && apt-get install -y \
    curl \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .

RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000

# Gunakan uvicorn tanpa --reload untuk production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
