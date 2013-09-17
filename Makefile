test:
	python setup.py test

flake8:
	flake8 --ignore=E501 --max-complexity 12 cio

install:
	python setup.py install

develop:
	python setup.py develop

coverage:
	coverage run --include=cio/* setup.py test
