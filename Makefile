# simple Makefile with scripts that are otherwise hard to remember
# to use, run from the repo root `make <command>`

default: help

help:
	@echo Developer commands:
	@echo
	@echo "  run				Run pulse app"
	@echo "  ruff               Run ruff, fixing any safely-fixable errors and formatting"
	@echo "  test               Run the unit tests."
	@echo "  generate 		    Generate migration files from models in pulse/app/db/models.py"
	@echo "  build              Build the project"
	@echo "  run                Run the application"
	@echo "  clean              Remove generated files"
	@echo "  serve              Start the docker-compose"
	@echo "  stop               Stop the docker-compose"
	@echo "  clean              Clean the docker-compose data"

# Runs pulse
run:
	python -m pulse.app.main

# Runs ruff, fixing any safely-fixable errors and formatting
ruff:
	ruff check . --fix
	ruff format .

# Run the unit tests
test:
	pytest -s ./tests

## -------------- DOCKER COMPOSE ---------

.PHONY: build serve stop clean

build:
	docker-compose build --no-cache

serve:
	docker-compose up -d --build

stop:
	docker-compose down

clean:
	docker-compose down -v