.PHONY: run build shell

DOCKER_COMPOSE_ARGS=-f docker-compose.base.yml -f docker-compose.yml

run:
	docker-compose $(DOCKER_COMPOSE_ARGS) run --rm --service-ports app

build:
	docker-compose $(DOCKER_COMPOSE_ARGS) build

test:
	docker-compose $(DOCKER_COMPOSE_ARGS) run --rm app ./manage.py test

shell:
	docker-compose $(DOCKER_COMPOSE_ARGS) run --rm --service-ports app bash
