.. image:: https://travis-ci.org/claws/aioprometheus.svg?branch=master
    :target: https://travis-ci.org/claws/aioprometheus

.. image:: https://img.shields.io/pypi/v/aioprometheus.svg
    :target: https://pypi.python.org/pypi/aioprometheus

aioprometheus
=============

`aioprometheus` is a Prometheus Python client library for asyncio-based
applications. It provides asyncio based applications with a metrics
collection and serving capability for use with the
`Prometheus <https://prometheus.io/>`_ monitoring and alerting system.
It supports multiple data formats and pushing metrics to a gateway.

The project source code can be found `here <https://github.com/claws/aioprometheus>`_.

.. warning::

    While this project is mostly in a usable state it is still very early in
    development. There are no backwards compatibility guarantees yet.

`aioprometheus` originates from the (now deprecated)
`prometheus python <https://github.com/slok/prometheus-python>`_ package.
Many thanks to `slok <https://github.com/slok>`_ for developing
prometheus-python. I have taken the original work and modified it to meet
the needs of my asyncio-based applications, added the histogram metric,
integrated the use of Pyrobuf, updated and extended tests, added docs, etc.


Contents
--------

.. toctree::
   :maxdepth: 1

   user/index
   dev/index
   api/index


License
-------

`aioprometheus` is released under the MIT license.

`aioprometheus` originates from the (now deprecated)
`prometheus python <https://github.com/slok/prometheus-python>`_ package which
was released under the MIT license. `aioprometheus` continues to use the MIT
license and contains a copy of the orignal MIT license from the
`prometheus-python` project as instructed by the original license.

