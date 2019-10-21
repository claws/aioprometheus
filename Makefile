# This makefile has been created to help developers perform common actions.
# It assumes it is operating in an environment, such as a virtual env,
# where the python command links to the Python3.6 executable.


# Do not remove this block. It is used by the 'help' rule when
# constructing the help output.
# help:
# help: aioprometheus Makefile help
# help:

VENVS_DIR := $(HOME)/.venvs
VENV_DIR := $(VENVS_DIR)/vap

# help: help                           - display this makefile's help information
.PHONY: help
help:
	@grep "^# help\:" Makefile | grep -v grep | sed 's/\# help\: //' | sed 's/\# help\://'


# help: venv                           - create a virtual environment for development
.PHONY: venv
venv:
	@test -d "$(VENVS_DIR)" || mkdir -p "$(VENVS_DIR)"
	@rm -Rf "$(VENV_DIR)"
	@python3 -m venv "$(VENV_DIR)"
	@/bin/bash -c "source $(VENV_DIR)/bin/activate && pip install pip --upgrade && pip install -r requirements.dev.txt"
	@/bin/bash -c "source $(VENV_DIR)/bin/activate && pip install -e ."
	@echo "Enter virtual environment using:\n\n\t$ source $(VENV_DIR)/bin/activate\n"


# help: clean                          - clean all files using .gitignore rules
.PHONY: clean
clean:
	@git clean -X -f -d


# help: clean.scrub                    - clean all files, even untracked files
.PHONY: clean.scrub
clean.scrub:
	git clean -x -f -d


# help: test                           - run tests
.PHONY: test
test:
	@python -m unittest discover -s tests


# help: test.verbose                   - run tests [verbosely]
.PHONY: test.verbose
test.verbose:
	@python -m unittest discover -s tests -v


# help: coverage                       - perform test coverage checks
.PHONY: coverage
coverage:
	@coverage run -m unittest discover -s tests
	@# produce html coverage report on modules
	@coverage html -d docs/coverage --include="src/aioprometheus/*"
	@# rename coverage html file for use with documentation
	@cd docs/coverage; mv index.html coverage.html


# help: style                          - perform code style format
.PHONY: style
style:
	@black src/aioprometheus tests examples


# help: check-style                    - check code format compliance
.PHONY: check-style
check-style:
	@black --check src/aioprometheus tests examples


# help: check_types                    - check type hint annotations
.PHONY: check_types
check_types:
	@cd src; MYPYPATH=$VIRTUAL_ENV/lib/python*/site-packages mypy -p aioprometheus --ignore-missing-imports


# help: docs                           - generate project documentation
.PHONY: docs
docs: coverage
	@cd docs; rm -rf api/aioprometheus*.rst api/modules.rst _build/*
	@cd docs; sphinx-apidoc -o ./api ../src/aioprometheus
	@cd docs; make html
	@cd docs; cp -R coverage _build/html/.


# help: docs.serve                     - serve HTML documentation
.PHONY: docs.serve
docs.serve:
	@cd docs; python -m http.server


# help: dist                           - create a wheel distribution package
.PHONY: dist
dist:
	@rm -rf dist
	@python setup.py bdist_wheel


# help: dist.test                      - test a wheel distribution package
.PHONY: dist.test
dist.test: dist
	@cd dist && ../tests/test_dist.bash ./aioprometheus-*-py3-none-any.whl


# help: dist.upload                    - upload a wheel distribution package
.PHONY: dist.upload
dist.upload:
	@twine upload dist/aioprometheus-*-py3-none-any.whl


# Keep these lines at the end of the file to retain nice help
# output formatting.
# help:
