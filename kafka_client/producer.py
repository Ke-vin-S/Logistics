from confluent_kafka import Producer
import json
import os
import logging

logger = logging.getLogger(__name__)

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")

producer = Producer({
    'bootstrap.servers': KAFKA_BROKER_URL
})

def delivery_report(err, msg):
    if err is not None:
        logger.error(f"Delivery failed for record {msg.key()}: {err}")
    else:
        logger.info(f"Record {msg.key()} successfully produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def publish_event(topic: str, key: str, payload: dict):
    try:
        producer.produce(
            topic=topic,
            key=key,
            value=json.dumps(payload),
            callback=delivery_report
        )
        producer.flush()  # ensures all messages are delivered before exiting
    except Exception as e:
        logger.error(f"[Kafka Error] Failed to publish to topic '{topic}': {e}")
