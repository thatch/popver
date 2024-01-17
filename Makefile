SRCS:=popver

.venv:
	python -m venv .venv
	source .venv/bin/activate && make setup dev
	echo 'run `source .venv/bin/activate` to use virtualenv'

.PHONY: venv
venv: .venv

.PHONY: dev
dev:
	flit install --symlink

.PHONY: setup
setup:
	python -m pip install -U pip
	python -m pip install -Ue '.[dev]'

.PHONY: release
release: lint test clean
	flit publish

.PHONY: lint
format:
	python -m ufmt format $(SRCS)

.PHONY: lint
lint:
	python -m mypy --strict --install-types --non-interactive $(SRCS)
	python -m flake8 $(SRCS)
	python -m ufmt check $(SRCS)

.PHONY: test
test:
	python -m coverage run -m $(SRCS).tests
	python -m coverage report
	python -m coverage html
	python -m doctest README.md

.PHONY: deps
deps:
	python -m pessimist -c 'python -m $(SRCS).tests' --requirements= --fast .

.PHONY: html
html: .venv README.md docs/*.rst docs/conf.py
	source .venv/bin/activate && sphinx-build -b html docs html

.PHONY: clean
clean:
	rm -rf build dist html README MANIFEST *.egg-info .mypy_cache

.PHONY: distclean
distclean: clean
	rm -rf .venv
