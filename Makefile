.PHONY: run buildserver runserver shell

run: runserver

buildserver:
	docker-compose build

runserver:
	docker-compose run --rm --service-ports app

shell:
	docker-compose run --rm --service-ports app bash
