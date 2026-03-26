"""
InfluxDB schema definitions — measurements, tags, fields, and retention.

Based on ET WEATHER PM2.5/H/T sensor. Fields are defaults until Wilfred confirms.
"""

# ── Measurement name ─────────────────────────────────────────────────────────
MEASUREMENT_TELEMETRY = "weather_telemetry"

# ── Tag keys (indexed, low-cardinality) ──────────────────────────────────────
TAG_DEVICE_ID = "device_id"
TAG_LOCATION = "location"

# ── Field keys (high-cardinality sensor values) ─────────────────────────────
FIELD_TEMPERATURE = "temperature"  # °C, float
FIELD_HUMIDITY = "humidity"        # %, float
FIELD_PM25 = "pm25"                # µg/m³, float

# All expected field keys (for validation)
EXPECTED_FIELDS = {
    FIELD_TEMPERATURE,
    FIELD_HUMIDITY,
    FIELD_PM25,
}

# ── Retention ────────────────────────────────────────────────────────────────
DEFAULT_RETENTION_DAYS = 30
