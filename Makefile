.PHONY: install run test clean

install:
	python -m pip install -e .

run:
	python -m adhd_ops.pipeline --root .

test:
	pytest

clean:
	rm -rf data/synthetic/* results/* models/* reports/*.html reports/*.md tableau/exports/*
