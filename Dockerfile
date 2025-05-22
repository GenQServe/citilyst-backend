FROM python:3.12-slim

# 1. Install system dependencies yang dibutuhkan oleh WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libffi-dev \
    libgobject-2.0-0 \
    libxml2 \
    libxslt1.1 \
    wget \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Upgrade pip dan install Python dependencies
RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 3. Salin seluruh source code
COPY . .

EXPOSE 8000

# 4. Jalankan Uvicorn tanpa auto-reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
