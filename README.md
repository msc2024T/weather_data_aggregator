🌦️ Weather Data Aggregator

An asynchronous Django REST API that fetches weather data for multiple cities using WeatherAPI
and manages requests through Celery, RabbitMQ, and Redis.

Features

Submit a request with multiple city names.

Asynchronous background task fetches weather data via WeatherAPI.

Each request is tracked with status (PENDING, SUCCESS, FAILED).

Stores weather results in the database.

Provides endpoints to:

Create new weather requests.

Retrieve request details and results.

List all weather requests.

Fully documented with Swagger UI and Redoc.

🛠️ Tech Stack

Backend: Django + Django REST Framework

Async Processing: Celery

Message Broker: RabbitMQ

Result Backend: Redis

API Docs: drf-yasg (Swagger + Redoc)

Database: SQLite for dev
