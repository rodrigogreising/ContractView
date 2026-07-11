.PHONY: start stop logs migrate seed reset health test
start:
	docker compose up --build -d
stop:
	docker compose down
logs:
	docker compose logs -f
migrate:
	docker compose run --rm api python -m app.manage migrate
seed:
	docker compose run --rm api python -m app.manage seed
reset:
	docker compose run --rm api python -m app.manage reset
health:
	curl --fail http://localhost:8000/health/ready
	curl --fail http://localhost:4173/
test:
	docker compose run --rm api pytest
	docker compose run --rm web-test
