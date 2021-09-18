.. image:: https://github.com/claws/aioprometheus/workflows/Python%20Package%20Workflow/badge.svg?branch=master
    :target: https://github.com/claws/aioprometheus/actions?query=branch%3Amaster

.. image:: https://img.shields.io/pypi/v/aioprometheus.svg
    :target: https://pypi.python.org/pypi/aioprometheus

.. image:: https://readthedocs.org/projects/aioprometheus/badge/?version=latest
    :target: https://aioprometheus.readthedocs.io/en/latest

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
  :target: https://github.com/ambv/black

aioprometheus
=============

.. toctree::
   :maxdepth: 1
   :hidden:

   user/index
   dev/index
   api/index

`aioprometheus` is a Prometheus Python client library for asyncio-based
applications. It provides metrics collection and serving capabilities for
use with `Prometheus <https://prometheus.io/>`_ and compatible monitoring
systems. It supports exporting metrics into text and binary formats and
pushing metrics to a gateway.

`aioprometheus` can be used in applications built with FastAPI/Starlette,
Quart, aiohttp as well as networking apps built upon asyncio.

See the :ref:`user-guide-label` for information about how to install and
use this package.

License
-------

`aioprometheus` is released under the MIT license.

`aioprometheus` originates from the (now deprecated)
`prometheus python <https://github.com/slok/prometheus-python>`_ package which
was released under the MIT license. `aioprometheus` continues to use the MIT
license and contains a copy of the orignal MIT license from the
`prometheus-python` project as instructed by the original license.


Origins
-------

`aioprometheus` originates from the (now deprecated)
`prometheus python <https://github.com/slok/prometheus-python>`_ package.
Many thanks to `slok <https://github.com/slok>`_ for developing
prometheus-python. I have taken the original work and modified it to meet
the needs of my asyncio-based applications, added the histogram metric,
integrated support for binary format, updated and extended tests, added docs,
decorators, etc.

