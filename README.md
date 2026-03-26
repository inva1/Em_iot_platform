# IoT Platform

Enterprise-style IoT Platform for real-time telemetry ingestion, device management, and dashboard visualization.

## Architecture

```
ESP32 ──TCP:9000──▶ PubSub_Server (Custom TCP Broker)
                         │
                    Apache Kafka (internal)
                    ┌────┴────┐
                    ▼         ▼
              iot.telemetry  iot.commands
                    │         │
                    ▼         ▼
              InfluxDB    Command Router
              Writer      (→ Broker → Device)
                    │
                    ▼
              InfluxDB 2.x ◀── Query API (:8080)
```

## Quick Start

```bash
# 1. Copy environment config
cp .env.example .env

# 2. Start all services
docker compose up -d

# 3. Check status
docker compose ps

# 4. View broker logs
docker compose logs -f broker
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| TCP Broker | 9000 | Device connections (custom binary protocol) |
| Query API | 8080 | REST API for telemetry queries |
| Kafka | 9092 | Internal message bus |
| InfluxDB | 8086 | Time-series database |

## Project Structure

```
Em_iot_platform/
├── PubSub_Server/          # TCP broker + Kafka + InfluxDB + API
│   ├── protocol/           # Binary protocol library (Library Design)
│   ├── broker/             # asyncio TCP server
│   ├── kafka_bridge/       # Kafka producer/consumer
│   ├── influxdb_layer/     # InfluxDB client, writer, queries
│   ├── api/                # FastAPI query endpoints
│   ├── main.py             # Entrypoint
│   └── Dockerfile
├── Pubsub_Client/          # Arduino C++ library (Library Design)
│   ├── src/                # IoTPubSubClient.h/.cpp
│   └── examples/           # Example sketch for ESP32
├── docs/                   # Protocol specification
├── docker-compose.yml      # Kafka + InfluxDB + broker
└── .env.example            # Configuration template
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| GET | `/api/v1/devices/{id}/telemetry` | Historical telemetry |
| GET | `/api/v1/devices/{id}/telemetry/latest` | Latest reading |

## Documentation

- [Protocol Design](docs/protocol_design.md) — Binary frame format, message types, topic structure
