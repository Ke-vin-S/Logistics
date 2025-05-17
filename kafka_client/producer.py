from kafka import KafkaProducer
import json
import os
import logging

logger = logging.getLogger(__name__)

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER_URL,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8") if k else None,
    linger_ms=10,
    retries=3,
)

def publish_event(topic: str, key: str, payload: dict):
    try:
        future = producer.send(topic, key=key, value=payload)
        result = future.get(timeout=10)  # optional: wait for delivery
        logger.info(f"Published to topic {topic}: {payload}")
        return result
    except Exception as e:
        logger.error(f"Failed to publish to Kafka topic '{topic}': {e}")
