import logging
import random
import time
import uuid

from flask import Blueprint, Response, current_app, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .metrics import (
    PAYMENT_ERRORS_TOTAL,
    PAYMENT_REQUEST_LATENCY,
    PAYMENT_REQUESTS_TOTAL,
)

logger = logging.getLogger(__name__)

bp = Blueprint("main", __name__)


@bp.get("/health")
def health():
    return jsonify({"status": "UP"})


@bp.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@bp.post("/api/payments")
def process_payment():
    PAYMENT_REQUESTS_TOTAL.inc()
    start_time = time.perf_counter()

    try:
        payload = request.get_json(force=False, silent=True)
        if payload is None:
            logger.warning("Invalid JSON received on /api/payments")
            return _error_response("Invalid JSON request body", 400)

        order_id = payload.get("orderId")
        amount = payload.get("amount")

        if order_id is None:
            logger.warning("Missing orderId in payment request")
            return _error_response("Missing required field: orderId", 400)

        if amount is None:
            logger.warning("Missing amount in payment request")
            return _error_response("Missing required field: amount", 400)

        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            logger.warning("Invalid amount type in payment request: %r", amount)
            return _error_response("Field 'amount' must be a number", 400)

        config = current_app.config
        latency_ms = random.uniform(config["MIN_LATENCY_MS"], config["MAX_LATENCY_MS"])
        time.sleep(latency_ms / 1000.0)

        logger.info("Processing payment for orderId=%s amount=%s", order_id, amount)

        if random.random() < config["FAILURE_RATE"]:
            PAYMENT_ERRORS_TOTAL.inc()
            logger.error("Payment DECLINED for orderId=%s", order_id)
            return (
                jsonify(
                    {
                        "status": "DECLINED",
                        "message": "Payment gateway unavailable",
                    }
                ),
                500,
            )

        transaction_id = str(uuid.uuid4())
        logger.info(
            "Payment APPROVED for orderId=%s transactionId=%s", order_id, transaction_id
        )
        return (
            jsonify(
                {
                    "status": "APPROVED",
                    "transactionId": transaction_id,
                    "amount": amount,
                }
            ),
            200,
        )
    finally:
        PAYMENT_REQUEST_LATENCY.observe(time.perf_counter() - start_time)


def _error_response(message: str, status_code: int):
    return jsonify({"status": "ERROR", "message": message}), status_code
