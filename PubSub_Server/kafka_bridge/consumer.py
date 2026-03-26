"""
Kafka consumer — consumes messages from Kafka topics and routes them.

Two consumers:
1. Telemetry consumer → writes to InfluxDB
2. Commands consumer → routes commands back through broker to devices
"""

import asyncio
import json
import logging
from typing import Optional, Callable, Awaitable

from confluent_kafka import Consumer, KafkaError, KafkaException

from config import config
from .topics import TOPIC_TELEMETRY, TOPIC_COMMANDS

logger = logging.getLogger(__name__)


class KafkaTopicConsumer:
    """
    Generic Kafka consumer that runs in a background task.
    Calls a message handler for each consumed message.
    """

    def __init__(
        self,
        topics: list[str],
        group_id: str,
        handler: Callable[[dict], Awaitable[None]],
        name: str = "consumer",
    ):
        self._topics = topics
        self._group_id = group_id
        self._handler = handler
        self._name = name
        self._consumer: Optional[Consumer] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        """Start the consumer in a background asyncio task."""
        kafka_config = {
            "bootstrap.servers": config.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": self._group_id,
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
            "auto.commit.interval.ms": 5000,
        }

        self._consumer = Consumer(kafka_config)
        self._consumer.subscribe(self._topics)
        self._running = True
        self._task = asyncio.get_event_loop().create_task(self._consume_loop())
        logger.info(
            f"Kafka {self._name} started — topics: {self._topics}, "
            f"group: {self._group_id}"
        )

    async def _consume_loop(self) -> None:
        """Main consume loop — runs until stopped."""
        loop = asyncio.get_event_loop()

        while self._running:
            try:
                # Poll in executor to avoid blocking the event loop
                msg = await loop.run_in_executor(
                    None, lambda: self._consumer.poll(1.0)
                )

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error(f"Kafka {self._name} error: {msg.error()}")
                    continue

                # Parse message
                try:
                    value = json.loads(msg.value().decode("utf-8"))
                    await self._handler(value)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from Kafka: {e}")
                except Exception as e:
                    logger.error(
                        f"Error in {self._name} handler: {e}", exc_info=True
                    )

            except Exception as e:
                if self._running:
                    logger.error(
                        f"Kafka {self._name} consume error: {e}", exc_info=True
                    )
                    await asyncio.sleep(1)  # backoff on error

    async def stop(self) -> None:
        """Stop the consumer."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self._consumer:
            self._consumer.close()
            logger.info(f"Kafka {self._name} stopped")
