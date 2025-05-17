from kafka import KafkaConsumer
import json
import os
import logging

logger = logging.getLogger(__name__)

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")

def start_consumer(topic: str, group_id: str = "default-group", auto_offset_reset: str = "latest"):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BROKER_URL,
        group_id=group_id,
        auto_offset_reset=auto_offset_reset,
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
    )

    logger.info(f"Listening to topic: {topic}")

    for message in consumer:
        logger.info(f"Received: Key={message.key}, Value={message.value}")
        handle_message(message.topic, message.key, message.value)

def handle_message(topic: str, key: str, value: dict):
    if topic == "shipment.status.updated":
        print(f"Shipment event for Order {key}: {value}")
