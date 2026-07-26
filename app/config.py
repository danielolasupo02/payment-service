import os


class Config:
    FAILURE_RATE = float(os.getenv("PAYMENT_FAILURE_RATE", "0.2"))
    MIN_LATENCY_MS = int(os.getenv("PAYMENT_MIN_LATENCY_MS", "100"))
    MAX_LATENCY_MS = int(os.getenv("PAYMENT_MAX_LATENCY_MS", "500"))
    RESOURCE_METRICS_INTERVAL_SEC = float(os.getenv("RESOURCE_METRICS_INTERVAL_SEC", "5"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
