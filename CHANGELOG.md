# Change Log

## 21.9.X

- Updated CI to support uploading code coverage results to CodeCov.
  Updated documentation to display codecov status badge.

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
