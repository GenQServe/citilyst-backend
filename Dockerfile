FROM python:3.12-alpine

RUN python3 -m pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .

RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000

# Gunakan uvicorn tanpa --reload untuk production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
