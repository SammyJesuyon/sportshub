.PHONY: up down logs migrate test test-api test-web test-web-quality test-e2e test-integration build clean

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f api web db

migrate:
	docker compose run --rm migrate

test: test-api test-web

test-api:
	cd sportshub-backend && python3 -m pytest

test-web:
	cd sportshub-frontend && npm test -- --run

test-web-quality:
	cd sportshub-frontend && npm run lint && npm run build

test-e2e:
	cd sportshub-frontend && npm run test:e2e

test-integration:
	docker compose --profile test run --rm api-test

build:
	docker compose build

clean:
	docker compose down --volumes --remove-orphans
