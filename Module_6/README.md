# Module 6 – Docker Microservices with RabbitMQ

A multi-service Flask + RabbitMQ + PostgreSQL + worker application using Docker Compose.

## Architecture

- **Web**: Flask application on port 8080
- **Worker**: Python consumer processing RabbitMQ tasks
- **Database**: PostgreSQL with named volume
- **Message Broker**: RabbitMQ with management UI on port 15672

## Prerequisites

- Docker Desktop
- Docker Compose

## Quick Start

```bash
# Clone the repository
git clone <your-repo-url>

# Start the stack
docker compose up --build

# Access the application
http://localhost:8080

# RabbitMQ Management UI
http://localhost:15672 (guest/guest)
## Docker Hub Images

- Web: [jsimsjhu/module_6-web:v1](https://hub.docker.com/r/jsimsjhu/module_6-web)
- Worker: [jsimsjhu/module_6-worker:v1](https://hub.docker.com/r/jsimsjhu/module_6-worker)

## Pull and Run

```bash
docker pull jsimsjhu/module_6-web:v1
docker pull jsimsjhu/module_6-worker:v1