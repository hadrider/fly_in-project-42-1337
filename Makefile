MAP ?= maps/map.txt

install:
	python3 -m pip install --user flake8 mypy

run:
	python3 main.py $(MAP)

run-no-visual:
	python3 main.py --no-visual $(MAP)

run-capacity:
	python3 main.py --capacity-info $(MAP)

debug:
	python3 -m pdb main.py $(MAP)

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true

.PHONY: install run run-no-visual run-capacity debug lint lint-strict clean
