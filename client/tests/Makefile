.PHONY: test

DOCKER_COMPOSE_ARGS=-f ../../server/docker-compose.base.yml -f docker-compose.yml

test:
	docker-compose $(DOCKER_COMPOSE_ARGS) up

build:
	docker-compose $(DOCKER_COMPOSE_ARGS) build
