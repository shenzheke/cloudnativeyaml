import json
import os
import time
import uuid
from flask import Flask, jsonify, request
from kafka import KafkaProducer

TOPIC = os.getenv("KAFKA_TOPIC", "flash-sale-orders")
producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP", "kafka.kafka-scenario.svc.cluster.local:9092"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    retries=5,
    acks="all",
)

app = Flask(__name__)


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"})


@app.post("/orders")
def create_order():
    payload = request.get_json(force=True, silent=True) or {}
    user_id = payload.get("user_id", "anonymous")
    sku = payload.get("sku", "sku-iphone-15")
    quantity = int(payload.get("quantity", 1))

    event = {
        "order_id": str(uuid.uuid4()),
        "user_id": user_id,
        "sku": sku,
        "quantity": quantity,
        "created_at": int(time.time() * 1000),
    }
    future = producer.send(TOPIC, key=sku.encode("utf-8"), value=event)
    metadata = future.get(timeout=10)

    return (
        jsonify(
            {
                "message": "order accepted and queued",
                "order_id": event["order_id"],
                "topic": metadata.topic,
                "partition": metadata.partition,
                "offset": metadata.offset,
            }
        ),
        202,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
