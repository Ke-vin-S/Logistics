import os
import json
import time
from confluent_kafka import Consumer, KafkaException

def consume_messages(topic, timeout=10, group_id="shipment-integration-tests"):
    consumer = Consumer({
        'bootstrap.servers': os.getenv("KAFKA_BROKER_URL", "localhost:9092"),
        'group.id': group_id,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': True,
    })

    consumer.subscribe([topic])
    end_time = time.time() + timeout
    messages = []

    try:
        while time.time() < end_time:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())

            key = msg.key().decode("utf-8") if msg.key() else None
            value = json.loads(msg.value().decode("utf-8"))
            print(f"[KAFKA] Got: {value}")
            messages.append(msg)

            # optional: stop early if messages are found
            if messages:
                break
    finally:
        consumer.close()

    return messages
