# This makefile has been created to help developers perform common actions.
# It assumes it is operating in an environment, such as a virtual env,
# where the python command links to the Python3.11 executable.


# Do not remove this block. It is used by the 'help' rule when
# constructing the help output.
# help:
# help: aioprometheus Makefile help
# help:

PYTHON_VERSION := python3.11
VENV_DIR := venv

# help: help                    - display this makefile's help information
.PHONY: help
help:
	@grep "^# help\:" Makefile | grep -v grep | sed 's/\# help\: //' | sed 's/\# help\://'


# help: venv                    - create a virtual environment for development
.PHONY: venv
venv:
	@rm -Rf "$(VENV_DIR)"
	@$(PYTHON_VERSION) -m venv "$(VENV_DIR)" --prompt aioprom
	@/bin/bash -c "source $(VENV_DIR)/bin/activate && pip install pip --upgrade && pip install -r requirements.dev.txt"
	@/bin/bash -c "source $(VENV_DIR)/bin/activate && pip install -e .[aiohttp,starlette,quart]"
	@echo "Enter virtual environment using:\n\n\t$ source $(VENV_DIR)/bin/activate\n"


# help: clean                   - clean all files using .gitignore rules
.PHONY: clean
clean:
	@git clean -X -f -d


# help: style                   - perform code style format
.PHONY: style
style:
	@isort . --profile black
	@black src/aioprometheus tests setup.py examples docs/conf.py


# help: test                    - run tests
.PHONY: test
test:
	@python -m unittest discover -s tests


# help: test-verbose            - run tests [verbosely]
.PHONY: test-verbose
test-verbose:
	@python -m unittest discover -s tests -v


# help: coverage                - perform test coverage checks
.PHONY: coverage
coverage:
	@coverage erase
	@rm -f .coverage.unit
	@COVERAGE_FILE=.coverage.unit coverage run -m unittest discover -s tests -v
	@coverage combine
	@coverage html
	@coverage report
	@coverage xml


# help: check-style             - check code style compliance
.PHONY: check-style
check-style:
	@isort . --check-only --profile black
	@black --check src/aioprometheus tests setup.py examples docs/conf.py


# help: check-lint              - check linting
.PHONY: check-lint
check-lint:
	@pylint --rcfile=.pylintrc aioprometheus setup.py ./examples ./docs/conf.py


# help: check-types             - check type hint annotations
.PHONY: check-types
check-types:
	@cd src; mypy -p aioprometheus --ignore-missing-imports


# help: checks                  - perform all checks
.PHONY: checks
checks: check-style check-lint check-types test


# help: docs                    - generate HTML documentation
.PHONY: docs
docs: coverage
	@cd docs; rm -rf api/aioprometheus*.rst api/modules.rst _build/*
	@cd docs; make html


# help: serve-docs              - serve HTML documentation
.PHONY: serve-docs
serve-docs:
	@cd docs/_build/html; python -m http.server


# help: dist                    - create a wheel distribution package
.PHONY: dist
dist:
	@rm -rf dist
	@python setup.py bdist_wheel


# help: test-dist               - test a wheel distribution package
.PHONY: test-dist
test-dist: dist
	@cd dist && ../tests/test_dist.bash ./aioprometheus-*-py3-none-any.whl


# help: upload-dist             - upload package wheel distribution
.PHONY: upload-dist
upload-dist:
	@twine upload dist/aioprometheus-*-py3-none-any.whl


# Keep these lines at the end of the file to retain nice help
# output formatting.
# help:
