from confluent_kafka import Consumer, KafkaException
import json
import os
import logging

logger = logging.getLogger(__name__)

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")

def start_consumer(topic: str, group_id: str = "default-group", auto_offset_reset: str = "latest"):
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BROKER_URL,
        'group.id': group_id,
        'auto.offset.reset': auto_offset_reset,
    })

    consumer.subscribe([topic])
    logger.info(f"Listening to topic: {topic}")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())

            value = json.loads(msg.value().decode("utf-8"))
            key = msg.key().decode("utf-8") if msg.key() else None
            handle_message(msg.topic(), key, value)
    except KeyboardInterrupt:
        print("Consumer stopped.")
    finally:
        consumer.close()

def handle_message(topic: str, key: str, value: dict):
    if topic == "shipment.status.updated":
        print(f"Shipment event for Order {key}: {value}")
