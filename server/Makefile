.PHONY: run build shell

run:
	docker-compose run --rm --service-ports app

build:
	docker-compose build

test:
	docker-compose run --rm app ./manage.py test

shell:
	docker-compose run --rm --service-ports app bash
