# payment-service

Minimal fake payment gateway microservice for a Kubernetes + Prometheus +
Grafana monitoring demo. Designed to run alongside a Java Spring Boot
`order-service`.

No database, auth, cache, queue, or external APIs — just simulated payment
processing with Prometheus metrics.

## Stack

- Python 3.12+
- Flask (application factory pattern)
- prometheus-client
- Gunicorn
- psutil (CPU/memory metrics)

## Project Structure

```
payment-service/
├── app/
│   ├── __init__.py   # create_app() factory
│   ├── routes.py     # /health, /api/payments, /metrics
│   ├── metrics.py    # Prometheus metrics + resource usage thread
│   └── config.py
├── requirements.txt
├── Dockerfile
├── gunicorn.conf.py
└── README.md
```

## Run Locally

```bash
pip install -r requirements.txt
gunicorn --config gunicorn.conf.py "app:create_app()"
```

Service listens on `http://localhost:8080`.

## Run with Docker

```bash
docker build -t payment-service .
docker run -p 8080:8080 payment-service
```

## Endpoints

### `GET /health`

Kubernetes liveness/readiness probe.

```json
{ "status": "UP" }
```

### `POST /api/payments`

Simulates payment processing:
- Random latency: 100–500ms
- ~20% random failure rate (`PAYMENT_FAILURE_RATE` env var)
- Success → HTTP 200, `APPROVED` + generated UUID `transactionId`
- Failure → HTTP 500, `DECLINED`

### `GET /metrics`

Prometheus exposition format.

## Metrics Exposed

| Metric | Type | Description |
|---|---|---|
| `payment_request_latency_seconds` | Summary | Payment request duration |
| `payment_errors_total` | Counter | Failed payment requests |
| `payment_requests_total` | Counter | Total payment requests received |
| `process_cpu_usage_percent` | Gauge | Process CPU usage % (updated every 5s) |
| `process_memory_usage_bytes` | Gauge | Process RSS memory in bytes |

No other custom metrics are exposed.

## Example curl Commands

Health check:
```bash
curl http://localhost:8080/health
```

Successful-style payment request:
```bash
curl -X POST http://localhost:8080/api/payments \
  -H "Content-Type: application/json" \
  -d '{"orderId": "12345", "amount": 2500}'
```

Missing field (validation error):
```bash
curl -X POST http://localhost:8080/api/payments \
  -H "Content-Type: application/json" \
  -d '{"orderId": "12345"}'
```

Invalid JSON:
```bash
curl -X POST http://localhost:8080/api/payments \
  -H "Content-Type: application/json" \
  -d 'not-json'
```

Metrics:
```bash
curl http://localhost:8080/metrics
```

## Environment Variables

| Var | Default | Purpose |
|---|---|---|
| `PAYMENT_FAILURE_RATE` | `0.2` | Fraction of payments that DECLINE |
| `PAYMENT_MIN_LATENCY_MS` | `100` | Min simulated latency |
| `PAYMENT_MAX_LATENCY_MS` | `500` | Max simulated latency |
| `RESOURCE_METRICS_INTERVAL_SEC` | `5` | CPU/memory sampling interval |
| `LOG_LEVEL` | `INFO` | Python logging level |

## Kubernetes Readiness Considerations

- Use `/health` for both `readinessProbe` and `livenessProbe` (it does no
  external I/O, so it's safe and fast for both).
- Suggested probe config:
  ```yaml
  readinessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 3
    periodSeconds: 5
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 5
    periodSeconds: 10
  ```
- Scale via **replicas**, not Gunicorn workers — this app runs a single
  Gunicorn worker per Pod because `prometheus-client`'s default registry is
  in-memory and not process-shared. Let Kubernetes handle horizontal scaling
  and Prometheus scrape each Pod individually (e.g. via a `ServiceMonitor` or
  `prometheus.io/scrape` pod annotations on port `8080`, path `/metrics`).
- Set CPU/memory `requests`/`limits` on the container; container should run
  as non-root (already handled via `USER appuser` in the Dockerfile).
- Pair with `order-service` in the same namespace/Service mesh; expose both
  under Prometheus scrape configs for a combined Grafana dashboard.
