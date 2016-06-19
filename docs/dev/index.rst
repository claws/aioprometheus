Developers Guide
================

The project is hosted on `GitHub <https://github.com/claws/aioprometheus>`_.
and uses `Travis <https://travis-ci.org/claws/aioprometheus>`_ for
Continuous Integration.

If you have found a bug or have an idea for an enhancement that would
improve the library, use the
`bug tracker <https://github.com/claws/aioprometheus/issues>`_.

To develop `aioprometheus` you'll need Python 3.5, some dependencies and
the source code.


Setup
-----

The best way to work on `aioprometheus` is to create a virtual env. This
isolates your work from other projects, dependencies and ensures that any
commands are pointing at the correct tools.

.. note::

    In the following example ``python`` is assumed to be the Python 3.5
    executable. You may need to explicitly specify this (e.g. use ``python3``)
    if you have multiple Python's available on your system.

.. code-block:: console

    $ python -m venv myvenv
    $ cd myvenv
    $ source bin/activate
    $ cd ..

To exit the virtual environment simply type ``deactivate``.

.. note::

    The following steps assume you are operating in a virtual environment.


Get the source
--------------

If you don't care about contributing back and just want the source then use:

.. code-block:: console

    $ git clone git@github.com:claws/aioprometheus.git

If you want to contribute changes back to the project you should first create a
fork of the `aioprometheus` repository and then clone the repo to your file-system.
Replace ``USER`` with your Github user name.

.. code-block:: console

    $ git clone git@github.com:USER/aioprometheus.git


Install Dependencies
--------------------

Install the developmental dependencies using ``pip``.

.. code-block:: console

    $ cd aioprometheus
    $ pip install -r requirements.dev.txt


Install aioprometheus
---------------------

Use ``pip`` to perform a development install of `aioprometheus`. This installs
the package in a way that allows you to edit the code after its installed and
have the changes take effect immediately.

.. code-block:: console

    $ pip install -e .


Test
----

The easiest method to run all of the unit tests is to run the ``make test``
rule from the top level directory. This runs the standard library
``unittest`` tool which discovers all the unit tests and runs them.

.. code-block:: console

    $ make test

Or, you can call the standard library unittest module directly.

.. code-block:: console

    $ python -m unittest discover -s tests -v

Individual unit tests can be run using the standard library ``unittest``
package too.

.. code-block:: console

    $ cd aioprometheus/tests
    $ python -m unittest test_negotiate


Documentation
-------------

To rebuild the project documentation, developers should run the ``make docs``
rule from the top level directory. It performs a number of steps to create
a new set of `sphinx <http://sphinx-doc.org/>`_ html content.

.. code-block:: console

    $ make docs

To quickly view the rendered docs locally as you are working you can use the
simple Python web server.

.. code-block:: console

    $ cd docs
    $ python -m http.server

Then open a browser to the `docs <http://localhost:8000/_build/html/index.html>`_
content.


Internals
---------

`Pyrobuf <https://github.com/appnexus/pyrobuf>`_ is used provide the Protobuf
Buffers based efficient binary formatting. Pyrobuf is a Cython based
implementation of the Protocol Buffers serialisation library. Pyrobuf does
not repuire `protoc`.

Extension modules created by ``pyrobuf`` are installed as separate packages.
When `aioprometheus` is installed you actually get two packages installed;
``aioprometheus`` and ``prometheus_metrics_proto``.

The Protocol Buffer specification used by `aioprometheus` was obtained from the
Prometheus `client model <https://github.com/prometheus/client_model/blob/master/metrics.proto>`_ repo.
