# Backend Assignment: FastAPI Webhook Service

This repository contains a FastAPI backend service for webhook ingestion, message storage, analytics, and observability. The service uses SQLite for storage, validates webhook HMAC signatures, and provides structured JSON logging and Prometheus metrics. The project is containerized with Docker and follows 12-factor app principles.

## Features

- POST /webhook: Validates HMAC SHA-256 signature, Pydantic payload, inserts messages once per message_id, returns 200 on duplicate, logs request metadata.
- GET /messages: Pagination (limit 1–100, default 50, offset default 0), filtering by sender, timestamp, or query, ordered by timestamp and message_id.
- GET /stats: Returns total messages, senders count, messages per sender, first and last timestamps.
- Health endpoints: /health/live always 200, /health/ready 200 only if DB reachable and WEBHOOK_SECRET exists.
- Metrics: Prometheus-compatible metrics including http_requests_total, webhook_requests_total, and latency buckets.
- JSON structured logging per request and webhook.

## Repository Structure

/app
  main.py
  models.py
  storage.py
  logging_utils.py
  metrics.py
  config.py
/tests
  test_webhook.py
  test_messages.py
  test_stats.py
Dockerfile
docker-compose.yml
Makefile
README.md

## Configuration

Set the following environment variables:

- WEBHOOK_SECRET: Secret for validating webhook HMAC signatures  
- DATABASE_URL: SQLite database URL (e.g., sqlite:///data/app.db)  
- LOG_LEVEL: Logging level (INFO, DEBUG, etc.)

## Running the Service

- Start with Docker Compose: `make up`  
- Stop: `make down`  
- View logs: `make logs`  
- Run tests: `make test`  

## API Endpoints

- POST /webhook: Validate and insert messages. Returns 200 on success or duplicate, 401 on invalid signature.  
- GET /messages: Retrieve paginated messages with filters.  
- GET /stats: Retrieve analytics about messages.  
- /health/live and /health/ready: Liveness and readiness checks.  
- /metrics: Prometheus metrics.

## Logging and Metrics

- JSON logs include ts, level, request_id, method, path, status, latency_ms, and webhook fields.  
- Prometheus metrics track HTTP requests, webhook calls, and latency buckets.

## Testing

Tests are written using pytest and cover webhook ingestion, messages retrieval, and stats endpoints. Run tests with `make test`.

## Design Decisions

- FastAPI for async, lightweight backend  
- SQLite for simple, idempotent storage  
- HMAC SHA-256 for secure webhooks  
- JSON structured logging for observability  
- 12-factor principles: env vars, logs to stdout, containerized  
- Docker and Docker Compose for production-like deployment
