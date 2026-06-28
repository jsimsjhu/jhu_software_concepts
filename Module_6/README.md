# Module 6 – Docker Microservices with RabbitMQ

A multi-service Flask + RabbitMQ + PostgreSQL + worker application using Docker Compose.

## Architecture

- **Web**: Flask application on port 8080
- **Worker**: Python consumer processing RabbitMQ tasks
- **Database**: PostgreSQL with named volume
- **Message Broker**: RabbitMQ with management UI on port 15672

## Prerequisites

- **Docker Desktop** (or Docker Engine + Docker Compose plugin)
  - Windows: Docker Desktop for Windows
  - macOS: Docker Desktop for Mac
  - Linux: Docker Engine + Docker Compose plugin
- Git

## Environment Variables

The following environment variables are used by the services:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://app_user:app_password@db:5432/postgres` |
| `RABBITMQ_URL` | RabbitMQ AMQP connection string | `amqp://guest:guest@rabbitmq:5672/` |

## Ports

| Service | Port | Description |
|---------|------|-------------|
| Web | 8080 | Flask application |
| RabbitMQ Management | 15672 | Web UI (guest/guest) |
| RabbitMQ AMQP | 5672 | Message broker |
| PostgreSQL | 5432 | Database |

## Quick Start

```bash
# Clone the repository
git clone <your-repo-url>
cd module_6

# Start the stack
docker compose up --build

# Access the application
http://localhost:8080

# RabbitMQ Management UI
http://localhost:15672 (guest/guest)