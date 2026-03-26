"""
Kafka topic name constants.
"""

# Sensor telemetry from devices (PUB on devices/{id}/telemetry)
TOPIC_TELEMETRY = "iot.telemetry"

# Device status events (online/offline)
TOPIC_DEVICE_STATUS = "iot.device_status"

# Commands to be routed to devices (from HTTP API → Kafka → broker → device)
TOPIC_COMMANDS = "iot.commands"
