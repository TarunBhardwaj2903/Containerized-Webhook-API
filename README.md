# FastAPI Service Assignment

A production-style FastAPI service for ingesting WhatsApp-like messages.

## Dependencies used
- FastAPI
- Uvicorn
- Pydantic
- SQLite
- Docker & Docker Compose

## Setup Used
VSCode + Copilot

## How to Run

### Prerequisites
- Docker & Docker Compose
- Make (optional, can use docker commands directly)

### Start the Service
```bash
make up
# OR
docker compose up -d --build
```
The service will be available at `http://localhost:8000`.

### Watch Logs
```bash
make logs
# OR
docker compose logs -f api
```

### Run Tests
```bash
make test
# OR
docker compose run --rm api pytest
```

### Stop Service
```bash
make down
# OR
docker compose down -v
```

## Endpoints

- **GET /**: Interactive Dashboard.
- **POST /webhook**: Ingest messages. Requires `X-Signature` header (HMAC-SHA256).
- **GET /messages**: List messages with pagination and filtering.
- **GET /stats**: View simple analytics.
- **GET /metrics**: Prometheus metrics.
- **GET /health/live**: Liveness probe.
- **GET /health/ready**: Readiness probe.

## Design Decisions

### HMAC Verification
Implemented in `app.main.webhook` using `hmac.compare_digest` to prevent timing attacks. The signature is computed as `hex(HMAC_SHA256(secret, raw_body_bytes))`. We read the raw body bytes first for signature verification before parsing JSON.

### Pagination Contract
The `/messages` endpoint accepts `limit` and `offset`. It returns a data array and a `total` count which reflects the number of records matching the filters, enabling frontend pagination UI to calculate total pages.

### Stats and Metrics
- **/stats**: Provides business-level analytics (top senders, total count) using SQL aggregation for efficiency.
- **/metrics**: Exposes operational metrics (req count, latency) in Prometheus format using a simple in-memory registry (`app.metrics`). This avoids adding a heavyweight dependency like `prometheus_client` for a simple requirement, keeping the image size small.
