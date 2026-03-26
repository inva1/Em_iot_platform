"""
InfluxDB 2.x client wrapper — connection management, bucket setup.
"""

import logging
from typing import Optional

from influxdb_client import InfluxDBClient, BucketRetentionRules
from influxdb_client.client.write_api import SYNCHRONOUS

from config import config
from .schema import DEFAULT_RETENTION_DAYS

logger = logging.getLogger(__name__)


class InfluxDBManager:
    """
    Manages the InfluxDB 2.x connection and provides write/query APIs.
    """

    def __init__(self):
        self._client: Optional[InfluxDBClient] = None
        self._write_api = None
        self._query_api = None

    def initialize(self) -> None:
        """Connect to InfluxDB and ensure the bucket exists."""
        try:
            self._client = InfluxDBClient(
                url=config.INFLUXDB_URL,
                token=config.INFLUXDB_TOKEN,
                org=config.INFLUXDB_ORG,
            )

            # Test connection
            health = self._client.health()
            if health.status != "pass":
                raise ConnectionError(f"InfluxDB unhealthy: {health.message}")

            self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
            self._query_api = self._client.query_api()

            # Ensure bucket exists
            self._ensure_bucket()

            logger.info(
                f"InfluxDB connected: {config.INFLUXDB_URL}, "
                f"org={config.INFLUXDB_ORG}, bucket={config.INFLUXDB_BUCKET}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB: {e}")
            raise

    def _ensure_bucket(self) -> None:
        """Create the telemetry bucket if it doesn't exist."""
        buckets_api = self._client.buckets_api()

        existing = buckets_api.find_bucket_by_name(config.INFLUXDB_BUCKET)
        if existing:
            logger.debug(f"Bucket '{config.INFLUXDB_BUCKET}' already exists")
            return

        retention_seconds = config.INFLUXDB_RETENTION_DAYS * 24 * 3600
        retention_rules = BucketRetentionRules(
            type="expire",
            every_seconds=retention_seconds,
        )

        buckets_api.create_bucket(
            bucket_name=config.INFLUXDB_BUCKET,
            retention_rules=retention_rules,
            org=config.INFLUXDB_ORG,
        )
        logger.info(
            f"Created InfluxDB bucket '{config.INFLUXDB_BUCKET}' "
            f"(retention: {config.INFLUXDB_RETENTION_DAYS} days)"
        )

    @property
    def write_api(self):
        """Get the write API."""
        if not self._write_api:
            raise RuntimeError("InfluxDB not initialized")
        return self._write_api

    @property
    def query_api(self):
        """Get the query API."""
        if not self._query_api:
            raise RuntimeError("InfluxDB not initialized")
        return self._query_api

    def close(self) -> None:
        """Close the InfluxDB connection."""
        if self._client:
            self._client.close()
            logger.info("InfluxDB connection closed")
