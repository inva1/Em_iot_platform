"""
InfluxDB Flux query helpers — functions for querying historical telemetry data.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from config import config
from .client import InfluxDBManager
from .schema import MEASUREMENT_TELEMETRY, TAG_DEVICE_ID

logger = logging.getLogger(__name__)


def query_device_telemetry(
    influx: InfluxDBManager,
    device_id: str,
    start: str = "-1h",
    stop: str = "now()",
    fields: Optional[list[str]] = None,
    limit: int = 1000,
    aggregate_window: Optional[str] = None,
) -> list[dict]:
    """
    Query historical telemetry for a device.

    Args:
        influx: InfluxDB manager instance.
        device_id: Device ID to query.
        start: Start time (Flux duration like '-1h', '-7d', or RFC3339).
        stop: Stop time (default 'now()').
        fields: Optional list of field names to filter (e.g. ['temperature', 'humidity']).
        limit: Maximum number of records.
        aggregate_window: Optional aggregation window (e.g. '5m', '1h').

    Returns:
        List of dicts with timestamp, field, value.
    """
    # Build Flux query
    flux = f'''
from(bucket: "{config.INFLUXDB_BUCKET}")
  |> range(start: {start}, stop: {stop})
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT_TELEMETRY}")
  |> filter(fn: (r) => r.{TAG_DEVICE_ID} == "{device_id}")
'''

    if fields:
        field_filter = " or ".join([f'r._field == "{f}"' for f in fields])
        flux += f'  |> filter(fn: (r) => {field_filter})\n'

    if aggregate_window:
        flux += f'  |> aggregateWindow(every: {aggregate_window}, fn: mean, createEmpty: false)\n'

    flux += f'  |> sort(columns: ["_time"], desc: true)\n'
    flux += f'  |> limit(n: {limit})\n'

    try:
        tables = influx.query_api.query(flux, org=config.INFLUXDB_ORG)

        results = []
        for table in tables:
            for record in table.records:
                results.append({
                    "time": record.get_time().isoformat(),
                    "field": record.get_field(),
                    "value": record.get_value(),
                    "device_id": record.values.get(TAG_DEVICE_ID, device_id),
                })

        return results

    except Exception as e:
        logger.error(f"InfluxDB query error for device '{device_id}': {e}")
        raise


def query_latest_telemetry(
    influx: InfluxDBManager,
    device_id: str,
) -> dict:
    """
    Get the latest telemetry reading for a device.

    Returns:
        Dict with field names as keys and latest values.
    """
    flux = f'''
from(bucket: "{config.INFLUXDB_BUCKET}")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT_TELEMETRY}")
  |> filter(fn: (r) => r.{TAG_DEVICE_ID} == "{device_id}")
  |> last()
'''

    try:
        tables = influx.query_api.query(flux, org=config.INFLUXDB_ORG)

        latest = {}
        latest_time = None
        for table in tables:
            for record in table.records:
                latest[record.get_field()] = record.get_value()
                if latest_time is None or record.get_time() > latest_time:
                    latest_time = record.get_time()

        if latest_time:
            latest["timestamp"] = latest_time.isoformat()
        latest["device_id"] = device_id

        return latest

    except Exception as e:
        logger.error(f"InfluxDB latest query error for '{device_id}': {e}")
        raise
