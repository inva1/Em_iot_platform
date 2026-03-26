"""
Kafka producer — sends messages from the broker to Kafka topics.

Flow: Device → TCP Broker → Kafka Producer → Kafka Topic
"""

import json
import logging
import time
from typing import Any, Optional

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

from config import config
from .topics import TOPIC_TELEMETRY, TOPIC_DEVICE_STATUS, TOPIC_COMMANDS

logger = logging.getLogger(__name__)


class KafkaMessageProducer:
    """Async-friendly Kafka producer for the broker."""

    def __init__(self):
        self._producer: Optional[Producer] = None
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the Kafka producer and ensure topics exist."""
        try:
            kafka_config = {
                "bootstrap.servers": config.KAFKA_BOOTSTRAP_SERVERS,
                "client.id": "iot-broker-producer",
                "acks": "all",
                "retries": 3,
                "retry.backoff.ms": 500,
            }
            self._producer = Producer(kafka_config)

            # Ensure topics exist
            self._ensure_topics()
            self._initialized = True
            logger.info(
                f"Kafka producer connected to {config.KAFKA_BOOTSTRAP_SERVERS}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self._initialized = False

    def _ensure_topics(self) -> None:
        """Create Kafka topics if they don't exist."""
        try:
            admin = AdminClient(
                {"bootstrap.servers": config.KAFKA_BOOTSTRAP_SERVERS}
            )
            topics = [
                NewTopic(TOPIC_TELEMETRY, num_partitions=3, replication_factor=1),
                NewTopic(TOPIC_DEVICE_STATUS, num_partitions=1, replication_factor=1),
                NewTopic(TOPIC_COMMANDS, num_partitions=3, replication_factor=1),
            ]
            futures = admin.create_topics(topics)
            for topic, future in futures.items():
                try:
                    future.result()
                    logger.info(f"Created Kafka topic: {topic}")
                except Exception as e:
                    # Topic may already exist — that's fine
                    if "already exists" in str(e).lower() or "TOPIC_ALREADY_EXISTS" in str(e):
                        logger.debug(f"Kafka topic '{topic}' already exists")
                    else:
                        logger.warning(f"Error creating topic '{topic}': {e}")
        except Exception as e:
            logger.warning(f"Could not ensure Kafka topics: {e}")

    def _delivery_callback(self, err, msg) -> None:
        """Callback for Kafka produce delivery reports."""
        if err:
            logger.error(f"Kafka delivery failed: {err}")
        else:
            logger.debug(
                f"Kafka message delivered to {msg.topic()} [{msg.partition()}]"
            )

    async def send_message(
        self, topic: str, payload: Any, device_id: str
    ) -> None:
        """
        Route a published message to the appropriate Kafka topic.

        Args:
            topic: The MQTT-style topic (e.g. 'devices/ESP32_01/telemetry')
            payload: The message payload (dict or any JSON-serializable)
            device_id: The publishing device's ID
        """
        if not self._initialized or not self._producer:
            logger.warning("Kafka producer not initialized — message dropped")
            return

        # Determine Kafka topic based on MQTT-style topic path
        if topic.endswith("/telemetry"):
            kafka_topic = TOPIC_TELEMETRY
        elif topic.endswith("/status"):
            kafka_topic = TOPIC_DEVICE_STATUS
        elif "commands/response" in topic:
            # Command responses could go to a separate topic or be logged
            kafka_topic = TOPIC_DEVICE_STATUS
        else:
            kafka_topic = TOPIC_TELEMETRY  # default fallback

        message = {
            "device_id": device_id,
            "topic": topic,
            "payload": payload,
            "timestamp": int(time.time() * 1000),
        }

        try:
            self._producer.produce(
                kafka_topic,
                key=device_id.encode("utf-8"),
                value=json.dumps(message).encode("utf-8"),
                callback=self._delivery_callback,
            )
            self._producer.poll(0)  # trigger delivery callbacks
        except Exception as e:
            logger.error(f"Kafka produce error: {e}")

    async def send_status(self, device_id: str, status: str) -> None:
        """Send a device status event (online/offline) to Kafka."""
        if not self._initialized or not self._producer:
            return

        message = {
            "device_id": device_id,
            "status": status,
            "timestamp": int(time.time() * 1000),
        }

        try:
            self._producer.produce(
                TOPIC_DEVICE_STATUS,
                key=device_id.encode("utf-8"),
                value=json.dumps(message).encode("utf-8"),
                callback=self._delivery_callback,
            )
            self._producer.poll(0)
        except Exception as e:
            logger.error(f"Kafka status produce error: {e}")

    def flush(self) -> None:
        """Flush pending messages."""
        if self._producer:
            self._producer.flush(timeout=5)

    def close(self) -> None:
        """Close the producer."""
        self.flush()
        logger.info("Kafka producer closed")
