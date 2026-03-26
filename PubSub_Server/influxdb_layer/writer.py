"""
InfluxDB writer — consumes telemetry from Kafka and writes to InfluxDB.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from influxdb_client import Point, WritePrecision

from config import config
from .client import InfluxDBManager
from .schema import (
    MEASUREMENT_TELEMETRY,
    TAG_DEVICE_ID,
    EXPECTED_FIELDS,
)

logger = logging.getLogger(__name__)


class TelemetryWriter:
    """
    Writes telemetry data points to InfluxDB.
    Used as a Kafka consumer handler.
    """

    def __init__(self, influx_manager: InfluxDBManager):
        self._influx = influx_manager

    async def handle_telemetry_message(self, message: dict) -> None:
        """
        Handle a telemetry message from Kafka and write to InfluxDB.

        Expected message format (from Kafka):
        {
            "device_id": "ESP32_01",
            "topic": "devices/ESP32_01/telemetry",
            "payload": {
                "temperature": 28.5,
                "humidity": 65.2,
                "pm25": 12.3,
                "timestamp": 1711396800000
            },
            "timestamp": 1711396800000
        }
        """
        device_id = message.get("device_id")
        payload = message.get("payload", {})

        if not device_id:
            logger.warning("Telemetry message missing device_id — skipping")
            return

        if not isinstance(payload, dict):
            logger.warning(
                f"Telemetry payload from '{device_id}' is not a dict — skipping"
            )
            return

        try:
            # Build InfluxDB point
            point = Point(MEASUREMENT_TELEMETRY)
            point.tag(TAG_DEVICE_ID, device_id)

            # Add sensor fields
            field_count = 0
            for field_name, field_value in payload.items():
                if field_name in ("device_id", "timestamp"):
                    continue  # skip metadata fields

                if isinstance(field_value, (int, float)):
                    point.field(field_name, float(field_value))
                    field_count += 1
                elif isinstance(field_value, str):
                    point.field(field_name, field_value)
                    field_count += 1

            if field_count == 0:
                logger.warning(
                    f"No valid fields in telemetry from '{device_id}' — skipping"
                )
                return

            # Set timestamp
            ts = payload.get("timestamp") or message.get("timestamp")
            if ts:
                # Convert milliseconds to datetime
                point.time(
                    datetime.fromtimestamp(ts / 1000, tz=timezone.utc),
                    WritePrecision.MS,
                )
            else:
                point.time(datetime.now(timezone.utc), WritePrecision.MS)

            # Write to InfluxDB
            self._influx.write_api.write(
                bucket=config.INFLUXDB_BUCKET,
                org=config.INFLUXDB_ORG,
                record=point,
            )

            logger.debug(
                f"Wrote telemetry from '{device_id}': {field_count} fields"
            )

        except Exception as e:
            logger.error(
                f"Error writing telemetry from '{device_id}' to InfluxDB: {e}",
                exc_info=True,
            )
