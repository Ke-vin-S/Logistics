import os

from kafka import KafkaConsumer
import json
import time

def consume_messages(topic, timeout=10, group_id="shipment-integration-tests"):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=os.getenv("KAFKA_BROKER_URL", "localhost:9092"),
        group_id=group_id,
        auto_offset_reset="earliest",  # optional: 'latest' if group is fresh
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
    )

    end_time = time.time() + timeout
    messages = []

    while time.time() < end_time:
        msg_pack = consumer.poll(timeout_ms=1000)
        for tp, msgs in msg_pack.items():
            for msg in msgs:
                print(f"[KAFKA] Got: {msg.value}")
                messages.append(msg)
        if messages:
            break  # optional: break as soon as some messages arrive
        time.sleep(0.5)

    return messages
