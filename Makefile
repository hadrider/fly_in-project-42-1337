# Makefile for Fly-in drone simulation

.PHONY: install run debug clean lint lint-strict

install:
	python3 -m pip install flake8 mypy pypdf

run:
	python3 main.py test_map.txt

debug:
	python3 -m pdb main.py test_map.txt

clean:
	rm -rf __pycache__ models/__pycache__ .mypy_cache

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict
