import logging
import threading

import psutil
from prometheus_client import Counter, Gauge, Summary

logger = logging.getLogger(__name__)

# 1. Request latency
PAYMENT_REQUEST_LATENCY = Summary(
    "payment_request_latency_seconds",
    "Time spent processing payment requests",
)

# 2. Error rate
PAYMENT_ERRORS_TOTAL = Counter(
    "payment_errors_total",
    "Total number of failed payment requests",
)

# 3. Request volume
PAYMENT_REQUESTS_TOTAL = Counter(
    "payment_requests_total",
    "Total number of payment requests received",
)

# 4. Resource usage
PROCESS_CPU_USAGE_PERCENT = Gauge(
    "process_cpu_usage_percent",
    "Current process CPU usage percent",
)
PROCESS_MEMORY_USAGE_BYTES = Gauge(
    "process_memory_usage_bytes",
    "Current process memory usage in bytes (RSS)",
)

_process = psutil.Process()
_stop_event = threading.Event()


def _update_resource_metrics(interval_sec: float) -> None:
    # Prime cpu_percent (first call always returns 0.0)
    _process.cpu_percent(interval=None)
    while not _stop_event.wait(interval_sec):
        try:
            PROCESS_CPU_USAGE_PERCENT.set(_process.cpu_percent(interval=None))
            PROCESS_MEMORY_USAGE_BYTES.set(_process.memory_info().rss)
        except Exception:
            logger.exception("Failed to update resource metrics")


def start_resource_metrics_updater(interval_sec: float) -> None:
    thread = threading.Thread(
        target=_update_resource_metrics,
        args=(interval_sec,),
        daemon=True,
        name="resource-metrics-updater",
    )
    thread.start()
    logger.info("Started resource metrics updater (interval=%ss)", interval_sec)
