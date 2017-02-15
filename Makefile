test:
	python setup.py test

flake8:
	flake8 cio

install:
	python setup.py install

develop:
	python setup.py develop

coverage:
	coverage run --source cio setup.py test && \
	coverage report

clean:
	rm -rf .tox/ dist/ *.egg *.egg-info .coverage
