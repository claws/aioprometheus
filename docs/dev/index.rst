Developers Guide
================

The project is hosted on `GitHub <https://github.com/claws/aioprometheus>`_.
and uses `GitHub Actions <https://github.com/claws/aioprometheus/actions>`_ for
Continuous Integration.

If you have found a bug or have an idea for an enhancement that would
improve the library, use the
`bug tracker <https://github.com/claws/aioprometheus/issues>`_.

To develop `aioprometheus` you'll need Python 3.6+, some dependencies and
the source code.


Get the source
--------------

.. code-block:: console

    $ git clone git@github.com:claws/aioprometheus.git
    $ cd aioprometheus


Setup
-----

The best way to work on `aioprometheus` is to create a virtual env. This
isolates your work from other project's dependencies and ensures that any
commands are pointing at the correct tools.

.. note::

    You may need to explicitly specify which Python to use if you have
    multiple Python's available on your system  (e.g. ``python3``,
    ``python3.8``).

.. code-block:: console

    $ python3 -m venv venv --prompt aioprom
    $ source venv/bin/activate
    (aioprom) $
    (aioprom) $ pip install pip --upgrade

.. note::

    The following steps assume you are operating in a virtual environment.

To exit the virtual environment simply type ``deactivate``.


Install Development Environment
-------------------------------

Rules in the convenience Makefile depend on the development dependencies
being installed. The development dependencies also include various web
application frameworks to assist verifying integration methods. Install the
developmental dependencies using ``pip``. Then install the `aioprometheus`
package (and its optional dependencies). in a way that allows you to edit the
code after it is installed so that any changes take effect immediately.

.. code-block:: console

    (aioprom) $ pip install -r requirements.dev.txt
    (aioprom) $ pip install -e .[aiohttp,binary]


Code Style
----------

This project uses the Black code style formatter and isort to sort imports
for consistent code style. A Makefile convenience rule is available to apply
code style compliance.

.. code-block:: console

    (aioprom) $ make style


Linting
-------

This project uses Pylint to perform static analysis. A Makefile convenience
rule is available to check linting.

.. code-block:: console

    (aioprom) $ make check-lint


Type Annotations
----------------

The code base uses type annotations to provide helpful typing information
that can improve code comprehension which can help with future enhancements.

The type annotations checker ``mypy`` should run cleanly with no warnings.

Use the Makefile convenience rule to check no issues are reported.

.. code-block:: console

    (aioprom) $ make check-types


Test
----

The easiest method to run all of the unit tests is to run the ``make test``
rule from the top level directory. This runs the standard library ``unittest``
tool which discovers all the unit tests and runs them.

.. code-block:: console

    (aioprom) $ make test

Or, you can call the standard library unittest module directly.

.. code-block:: console

    (aioprom) $ python -m unittest discover -s tests -v

Individual unit tests can be run using the standard library ``unittest``
package too.

.. code-block:: console

    (aioprom) $ cd aioprometheus/tests
    (aioprom) $ python -m unittest test_negotiate


Coverage
--------

A Makefile convenience rule is available to check how much of the code is
covered by tests.

.. code-block:: console

    (aioprom) $ make coverage

The test code coverage report can be found `here <../_static/coverage/index.html>`_


Documentation
-------------

To rebuild the project documentation, developers should run the ``make docs``
rule from the top level directory. It performs a number of steps to create
a new set of `sphinx <http://sphinx-doc.org/>`_ html content.

.. code-block:: console

    (aioprom) $ make docs

To view the rendered docs locally run the ``serve-docs`` rule from the top level
directory to start a simple Python web server.

.. code-block:: console

    (aioprom) $ make serve-docs

Then open a browser to the `docs <http://localhost:8000/_build/html/index.html>`_
content.


.. _version-label:

Version
-------

`aioprometheus` uses a three segment `CalVer <http://calver.org/>`_ versioning
scheme comprising a short year, a zero padded month and then a micro version.
The ``YY.MM`` part of the version are treated similarly to a SemVer major
version. So when backwards incompatible or major functional changes occur the
``YY.MM`` will be rolled up. For all other minor changes only the micro part
will be incremented.


Release Process
---------------

Assuming that the tests are passing, the docs build without warnings and the
type annotations check passes without warnings then a release can be made.

The following steps are used to make a new software release:

- Ensure that the version label in ``__init__.py`` is correct. It must comply
  with the :ref:`version-label` scheme.

- Create the distribution. This project produces an artefact called a pure
  Python wheel. Only Python3 is supported by this package.

  .. code-block:: console

      (aioprom) $ make dist

- Test distribution. This involves creating a virtual environment, installing
  the distribution in it and running the tests. These steps have been captured
  for convenience in a Makefile rule.

  .. code-block:: console

      (aioprom) $ make test-dist

- Upload to PyPI using

  .. code-block:: console

      (aioprom) $ make upload-dist

- Create and push a repo tag to Github.

  .. code-block:: console

      $ git tag YY.MM.MICRO -m "A meaningful release tag comment"
      $ git tag  # check release tag is in list
      $ git push --tags origin master

  - Github will create a release tarball at:

    ::

        https://github.com/{username}/{repo}/tarball/{tag}.tar.gz
