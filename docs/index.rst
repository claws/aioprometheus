aioprometheus
=============

|ci status| |pypi| |python| |cov| |docs| |license|

.. toctree::
   :maxdepth: 1
   :hidden:

   user/index
   dev/index
   api/index
   changes/index

`aioprometheus` is a Prometheus Python client library for asyncio-based
applications. It provides metrics collection and serving capabilities for
use with `Prometheus <https://prometheus.io/>`_ and compatible monitoring
systems. It supports exporting metrics into text format and pushing metrics
to a gateway.

`aioprometheus` can be used in applications built with FastAPI/Starlette,
Quart, aiohttp as well as networking apps built upon asyncio.

See the :ref:`user-guide-label` for information about how to install and
use this package.

License
-------

`aioprometheus` is released under the MIT license. It is based upon the (now
deprecated) `prometheus python <https://github.com/slok/prometheus-python>`_
package which was released under the MIT license. A copy of the original MIT
license from the `prometheus-python` project is included as instructed by the
original license.


Origins
-------

`aioprometheus` originates from the (now deprecated) `prometheus python`
package. Many thanks to `slok <https://github.com/slok>`_ for developing
`prometheus-python`.

The original work has been modified and updated to support the needs of
asyncio applications by adding the histogram metric, docs, decorators, ASGI
middleware, etc.


.. |ci status| image:: https://github.com/claws/aioprometheus/workflows/CI%20Pipeline/badge.svg?branch=master
    :target: https://github.com/claws/aioprometheus/actions?query=branch%3Amaster

.. |pypi| image:: https://img.shields.io/pypi/v/aioprometheus.svg
    :target: https://pypi.python.org/pypi/aioprometheus

.. |python| image:: https://img.shields.io/pypi/pyversions/aioprometheus.svg
    :target: https://pypi.python.org/pypi/aioprometheus/

.. |cov| image:: https://codecov.io/github/claws/aioprometheus/branch/master/graph/badge.svg?token=oPPBg8hBgc
    :target: https://codecov.io/github/claws/aioprometheus

.. |docs| image:: https://readthedocs.org/projects/aioprometheus/badge/?version=latest
    :target: https://aioprometheus.readthedocs.io/en/latest

.. |license| image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target: https://github.com/claws/aioprometheus/License/LICENSE
