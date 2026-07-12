.PHONY: start stop logs migrate seed reset health test journey11-headless journey11-headed
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
journey11-headless:
	bash scripts/run_journey11.sh headless
journey11-headed:
	bash scripts/run_journey11.sh headed
