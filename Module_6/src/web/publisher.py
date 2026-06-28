"""RabbitMQ publisher for Flask web service."""

import os
import json
from datetime import datetime
import pika

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "tasks"


def _open_channel():
    """Open RabbitMQ channel and declare durable entities."""
    params = pika.URLParameters(RABBITMQ_URL)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
    return conn, ch


def publish_task(kind: str, payload: dict = None, headers: dict = None) -> None:
    """Publish a task to RabbitMQ."""
    if payload is None:
        payload = {}
    if headers is None:
        headers = {}

    body = {
        "kind": kind,
        "ts": datetime.utcnow().isoformat(),
        "payload": payload
    }

    conn, ch = _open_channel()
    try:
        ch.basic_publish(
            exchange=EXCHANGE,
            routing_key=ROUTING_KEY,
            body=json.dumps(body, separators=(",", ":")).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent message
                headers=headers
            ),
            mandatory=False
        )
    finally:
        conn.close()
