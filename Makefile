.PHONY: prerequisites start stop logs migrate seed reset api worker web health status test journey11-headless journey11-headed
prerequisites:
	bash scripts/poc.sh prerequisites
start:
	bash scripts/poc.sh start
stop:
	bash scripts/poc.sh stop
logs:
	bash scripts/poc.sh logs
migrate:
	bash scripts/poc.sh migrate
seed:
	bash scripts/poc.sh seed
reset:
	bash scripts/poc.sh reset
api:
	bash scripts/poc.sh api
worker:
	bash scripts/poc.sh worker
web:
	bash scripts/poc.sh web
health:
	bash scripts/poc.sh health
status:
	bash scripts/poc.sh status
test:
	docker compose run --rm api pytest
	docker compose run --rm web-test
journey11-headless:
	bash scripts/poc.sh certify-headless "$(EVIDENCE_DIR)"
journey11-headed:
	bash scripts/poc.sh record-headed "$(EVIDENCE_DIR)"
