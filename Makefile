# simple Makefile with scripts that are otherwise hard to remember
# to use, run from the repo root `make <command>`

default: help

help:
	@echo Developer commands:
	@echo
	@echo "ruff                     Run ruff, fixing any safely-fixable errors and formatting"
	@echo "test                     Run the unit tests."


# Runs ruff, fixing any safely-fixable errors and formatting
ruff:
	ruff check . --fix
	ruff format .

# Run the unit tests
test:
	pytest ./tests