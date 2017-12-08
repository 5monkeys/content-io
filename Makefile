.DEFAULT_GOAL := help

.PHONY: help  # shows available commands
help:
	@echo "\nAvailable commands:\n\n $(shell sed -n 's/^.PHONY:\(.*\)/ *\1\\n/p' Makefile)"

.PHONY: test
test:
	coverage run setup.py test

.PHONY: test_all  # runs tests using detox, combines coverage and reports it
test_all:
	detox
	make coverage

.PHONY: lint
lint:
	flake8 cio

.PHONY: install
install:
	python setup.py install

.PHONY: develop
develop:
	python setup.py develop

.PHONY: coverage
coverage:
	coverage combine || true
	coverage report

.PHONY: clean
clean:
	rm -rf .tox/ dist/ *.egg *.egg-info .coverage
