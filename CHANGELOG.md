# Change Log

## 22.4.0

- Fix package install issue related to pip when running ci jobs (#78)
- Use orjson instead of the standard python JSON library to speed up
  MetricDict (#77)
- Add support for aiohttp client args for various Pusher methods (#75)

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
