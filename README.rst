.. image:: https://travis-ci.org/claws/aioprometheus.svg?branch=master
    :target: https://travis-ci.org/claws/aioprometheus

.. image:: https://img.shields.io/pypi/v/aioprometheus.svg
    :target: https://pypi.python.org/pypi/aioprometheus


aioprometheus
=============

`aioprometheus` is a Prometheus Python client library for asyncio-based
applications. It provides metrics collection and serving capabilities,
supports multiple data formats and pushing metrics to a gateway.

The project documentation can be found on
`ReadTheDocs <http://aioprometheus.readthedocs.org/>`_.


Install
-------

.. code-block:: console

    $ pip install aioprometheus


Example
-------

The following example shows the ``@timer`` decorator being used to expose
a metric to Prometheus that measures how long a particular function takes
to execute.

.. code-block:: python3

    import asyncio
    import random

    from aioprometheus import Service, Summary, timer


    # Create a metric to track time spent and requests made.
    REQUEST_TIME = Summary(
        'request_processing_seconds', 'Time spent processing request')


    # Decorate function with metric.
    @timer(REQUEST_TIME)
    async def handle_request(duration):
        ''' A dummy function that takes some time '''
        await asyncio.sleep(duration)


    async def handle_requests():
        # Start up the server to expose the metrics.
        await svr.start(port=8000)
        # Generate some requests.
        while True:
            await handle_request(random.random())


    if __name__ == '__main__':

        loop = asyncio.get_event_loop()

        svr = Service(loop=loop)
        svr.registry.register(REQUEST_TIME)

        try:
            loop.run_until_complete(handle_requests())
        except KeyboardInterrupt:
            pass
        finally:
            loop.run_until_complete(svr.stop())
        loop.stop()
        loop.close()



License
-------

`aioprometheus` is released under the MIT license.

`aioprometheus` originates from the (now deprecated)
`prometheus python <https://github.com/slok/prometheus-python>`_ package which
was released under the MIT license. `aioprometheus` continues to use the MIT
license and contains a copy of the orignal MIT license from the
`prometheus-python` project as instructed by the original license.
