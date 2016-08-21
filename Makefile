# This makefile has been created to help developers perform common actions.
# It assumes it is operating in an environment, such as a virtual env,
# where the python command links to Python3.5 executable.

.PHONY: check_types clean clean.scrub coverage docs dist help
.PHONY: sdist style style.fix test test.verbose

# Do not remove this block. It is used by the 'help' rule when
# constructing the help output.
# help:
# help: aioprometheus Makefile help
# help:

STYLE_EXCLUDE_LIST:=git status --porcelain --ignored | grep "!!" | grep ".py$$" | cut -d " " -f2 | tr "\n" ","
STYLE_MAX_LINE_LENGTH:=160
STYLE_CMD:=pycodestyle --exclude=.git,docs,$(shell $(STYLE_EXCLUDE_LIST)) --ignore=E309,E402 --max-line-length=$(STYLE_MAX_LINE_LENGTH) aioprometheus tests examples


# help: help                           - display this makefile's help information
help:
	@grep "^# help\:" Makefile | grep -v grep | sed 's/\# help\: //' | sed 's/\# help\://'


# help: clean                          - clean all files using .gitignore rules
clean:
	@git clean -X -f -d


# help: clean.scrub                    - clean all files, even untracked files
clean.scrub:
	git clean -x -f -d


# help: test                           - run tests
test:
	@python -m unittest discover -s tests


# help: test.verbose                   - run tests [verbosely]
test.verbose:
	@python -m unittest discover -s tests -v


# help: coverage                       - perform test coverage checks
coverage:
	@coverage run -m unittest discover -s tests
	@# produce html coverage report on modules
	@coverage html -d docs/coverage --include="aioprometheus/*"
	@# rename coverage html file for use with documentation
	@cd docs/coverage; mv index.html coverage.html


# help: style                          - perform pep8 check
style:
	@$(STYLE_CMD)


# help: style.fix                      - perform check with autopep8 fixes
style.fix:
	@# If there are no files to fix then autopep8 typically returns an error
	@# because it did not get passed any files to work on. Use xargs -r to
	@# avoid this problem.
	@$(STYLE_CMD) -q  | xargs -r autopep8 -i --max-line-length=$(STYLE_MAX_LINE_LENGTH)


# help: check_types                    - check type hint annotations
check_types:
	@MYPYPATH=$VIRTUAL_ENV/lib/python3.5/site-packages mypy -p aioprometheus --fast-parser -s


# help: docs                           - generate project documentation
docs: coverage
	@cd docs; rm -rf api/aioprometheus*.rst api/modules.rst _build/*
	@cd docs; sphinx-apidoc -o ./api ../aioprometheus
	@cd docs; make html
	@cd docs; cp -R coverage _build/html/.


# help: dist                           - create a source distribution package
dist: clean
	@python setup.py sdist


# help: dist.test                     - test a source distribution package
dist.test: dist
	@cd dist && ./test.bash ./aioprometheus-*.tar.gz


# help: dist.upload                    - upload a source distribution package
dist.upload: clean
	@python setup.py sdist upload


# Keep these lines at the end of the file to retain nice help
# output formatting.
# help:
