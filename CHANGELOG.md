# Change Log

## XX.Y.Z

## 23.3.0

- Added support for Histogram metric in timer decorator
- Update docs to demonstrate how to use basic authentication with Pusher.
- Developer updates
  - Removed isort optional extra 'deprecated_imports_finder' as it isn't supported anymore.
  - Minor type annotations updates to keep mypy happy
  - Updated '.pylintrc' to fix warnings about options that are no longer supported.
  - Updated Sphinx config to specify language to avoid warning being reported.
  - Minor updates to address pylint warnings
    - Silence orjson no-members warnings (See: https://github.com/ijl/orjson/issues/248)
  - Added httpx as developmental dependency so that the Starlette test client can be used.
    - Update ASGI middleware to obtain starlette app reference from 'http' ASGI scope when run from Starlette test client.
  - Updated Pusher unit test to check basic authentication.
    - Added aiohttp_basicauth to dev dependencies.
  - Fix CI
    - Removed support for Python3.6 as it isn't supported by Github actions anymore.
      - Updated repo to indicate minimum supported Python is 3.8+
    - Removed dependency on asynctest package which is no longer maintained and causes errors in Python3.11.
      - Using 'unittest.IsolatedAsyncioTestCase' instead, but this is only supported for 3.8+.
    - Updated CI workflow 'uses' items to use later versions
- Prometheus 2.0 removed support for the binary protocol. Removed support for Prometheus binary protocol (fixes #57).
  - Updated unit tests
  - Updated CI
  - Updated docs
  - Updated examples

## 22.5.0

- Fix CI package install issue related to pip (#78)

- Update Pusher to accept 'kwargs' to provide custom configuration to aiohttp
  client (#75)

- Use orjson instead of standard json to improve performance by speeding up
  MetricDict (#77) when rendering.

- Add a scheduled CI job to periodically verify unpinned dependencies (e.g. pip)
  continue to work as expected.

- Updated Quart unit test to fix issue which would result in a test failing if the
  optional 'binary' package was not installed.

- Update package version to 22.5.0

## 22.3.0

- Minor tweaks to project files such as setup.py formatting, Makefile rule
  streamlining, docs updates.

- Improve ASGI middleware integration with Starlette. Due to a implementation
  limitation the aioprometheus ASGI middleware needed to be added as the last
  middleware to avoid triggering an exception when Starlette rebuilds the
  middleware stack. To avoid this issue the middleware metrics are now all
  created upon the first call to update a metric.

- Fix ASGI middleware to allow a custom registry to be passed in.

- Fix ASGI middleware to allow custom const_labels to be passed in.

## 21.9.1

- Add Python 3.10 to CI testing.

- Updated package to support PEP561.

- Updated CI to support uploading code coverage results to CodeCov.
  Updated documentation to display codecov status badge.

- Added option to ASGI middleware that allows response status codes to
  be grouped. For example, status codes 200, 201, etc will all be reported
  under the group 2xx. Similar situation for 3xx, 4xx, 5xx.

- Added test that confirms the default ASGI metrics tracking exceptions
  raised by user handler functions does not work for Quart. Added information
  to user guide stating this.

- Added information to user guide for developers writing unit tests to be
  familiar with ``REGISTRY.clear()`` that will reset the default metrics
  registry to an empty state to avoid errors related to identical metrics
  attempting to be registered with the default registry.

## 21.9.0

- Streamline the aioprometheus API so that metrics are automatically registered
  when they are created. When a user creates a new metric they have the
  opportunity to specify a registry that the metric should be added to. If no
  registry is specified then the metric will be registered with the default
  registry. This simplifies the metrics creation process.

- Changed which modules are imported. Instead of default importing everything
  and having the accommodate for optional dependencies this update make a user
  explicitly import the modules that depend of optional dependencies. This
  simplifies the package implementation.

- Updated documentation to improve clarity and to use the sphinx_material theme.

- Improved test coverage. Removed unused code.

- Updated unit tests to gracefully handle when optional extras are not installed.
  This specifically helps run tests on Python 3.6 where Quart is not supported.
