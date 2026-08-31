# Prérequis : uv (https://docs.astral.sh/uv/)
UV ?= uv

setup:
	$(UV) sync --locked --all-extras

test:             ## 46 tests fermés, sans réseau
	$(UV) run pytest

lint:
	$(UV) run ruff check .

all:              ## tout : les exemples du régulateur, la structure, l'exigence, la couverture
	$(UV) run fdg tout
