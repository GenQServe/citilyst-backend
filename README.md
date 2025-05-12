# Citilyst Api services

## Start Locally

To start locally execute:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000  --log-level debug --reload
```

or

```bash
make start
```

## Docker Single

To build and start docker in single mode:

```bash
docker build -f Dockerfile.web -t citilyst-app .
docker run --rm -v ./:/app -p 8000:8000 citilyst-app
```

or

```bash
make docker-single-build
make docker-single-start
```

## Docker Compose

To build and start docker compose with application and database:

```bash
docker compose build
docker compose up -d
```

or

```bash
make docker-compose-build
make docker-compose-start
```

To stop docker compose:

```bash
docker compose down
```

or

```bash
make docker-compose-stop
```

