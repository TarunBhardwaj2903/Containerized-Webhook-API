.PHONY: up down logs test clean

up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f api

test:
	docker compose run --rm api pytest

clean:
	docker compose down -v
	rm -rf __pycache__ .pytest_cache
