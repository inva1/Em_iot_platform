"""
Global configuration loaded from environment variables.
"""

import os


class Config:
    """Platform configuration from environment variables with sensible defaults."""

    # ── Broker ───────────────────────────────────────────────────────────────
    BROKER_HOST: str = os.getenv("BROKER_HOST", "0.0.0.0")
    BROKER_PORT: int = int(os.getenv("BROKER_PORT", "9000"))

    # ── Kafka ────────────────────────────────────────────────────────────────
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC_TELEMETRY: str = os.getenv("KAFKA_TOPIC_TELEMETRY", "iot.telemetry")
    KAFKA_TOPIC_COMMANDS: str = os.getenv("KAFKA_TOPIC_COMMANDS", "iot.commands")
    KAFKA_TOPIC_DEVICE_STATUS: str = os.getenv("KAFKA_TOPIC_DEVICE_STATUS", "iot.device_status")
    KAFKA_CONSUMER_GROUP: str = os.getenv("KAFKA_CONSUMER_GROUP", "iot-platform")

    # ── InfluxDB ─────────────────────────────────────────────────────────────
    INFLUXDB_URL: str = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    INFLUXDB_TOKEN: str = os.getenv("INFLUXDB_TOKEN", "my-super-secret-token")
    INFLUXDB_ORG: str = os.getenv("INFLUXDB_ORG", "iot-platform")
    INFLUXDB_BUCKET: str = os.getenv("INFLUXDB_BUCKET", "telemetry")
    INFLUXDB_RETENTION_DAYS: int = int(os.getenv("INFLUXDB_RETENTION_DAYS", "30"))

    # ── Auth (backend API for token verification) ────────────────────────────
    # Peem's backend endpoint — stubbed until confirmed
    AUTH_VERIFY_URL: str = os.getenv(
        "AUTH_VERIFY_URL",
        "http://localhost:8081/api/internal/verify-device"
    )
    AUTH_TIMEOUT: int = int(os.getenv("AUTH_TIMEOUT", "5"))

    # ── Query API ────────────────────────────────────────────────────────────
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8080"))

    # ── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()
