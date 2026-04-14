.PHONY: help build up down logs shell test clean

help:
	@echo "Rabit Backend - Docker Commands"
	@echo "================================"
	@echo "make build       - Build Docker image"
	@echo "make up          - Start containers"
	@echo "make down        - Stop containers"
	@echo "make logs        - View container logs"
	@echo "make shell       - Open shell in container"
	@echo "make test        - Run tests"
	@echo "make clean       - Clean up containers and images"
	@echo "make env         - Create .env from .env.example"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f rabit-backend

shell:
	docker-compose exec rabit-backend /bin/bash

test:
	docker-compose exec rabit-backend python -m pytest

clean:
	docker-compose down -v
	docker system prune -f

env:
	cp .env.example .env
	@echo ".env file created. Please update with your values."

rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
