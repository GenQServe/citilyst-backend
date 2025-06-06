FROM python:3.12

# Install system dependencies WeasyPrint
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     libpangocairo-1.0-0 \
#     libpangoft2-1.0-0 \
#     libgdk-pixbuf2.0-0 \
#     libcairo2 \
#     libffi-dev \
#     libgobject-2.0-0 \
#     libxml2 \
#     libxslt1.1 \
#     wget \
#     curl \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .

RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000

# Gunakan uvicorn tanpa --reload untuk production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
