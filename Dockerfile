FROM python:3.12


RUN python3 -m pip install --upgrade pip

RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libgobject-2.0-0 \
    libffi-dev \
    shared-mime-info \
    # Tambahkan dependensi sistem lain yang mungkin dibutuhkan aplikasi Anda di sini
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000

# Gunakan uvicorn tanpa --reload untuk production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
