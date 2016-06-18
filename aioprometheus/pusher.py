
import asyncio

import aiohttp

from urllib.parse import urljoin
from aiohttp.hdrs import ACCEPT, CONTENT_TYPE
from .formats import BinaryFormatter


class Pusher(object):
    ''' This class is used to push a registry to a pushgateway '''

    PATH = "/metrics/jobs/{0}"
    INSTANCE_PATH = "/metrics/jobs/{0}/instances/{1}"

    def __init__(self, job_name, addr, instance_name=None, loop=None):
        self.job_name = job_name
        self.instance_name = instance_name
        self.addr = addr
        self.loop = loop or asyncio.get_event_loop()

        self.formatter = BinaryFormatter()
        self.headers = self.formatter.get_headers()

        # Set paths
        if instance_name:
            self.path = urljoin(self.addr, self.INSTANCE_PATH).format(
                job_name, instance_name)
        else:
            self.path = urljoin(self.addr, self.PATH).format(job_name)

    async def add(self, registry):
        """ Add works like replace, but only previously pushed metrics with the
            same name (and the same job and instance) will be replaced.
        """
        with aiohttp.ClientSession(loop=self.loop) as session:
            payload = self.formatter.marshall(registry)
            resp = await session.post(
                self.path, data=payload, headers=self.headers)
        await resp.release()
        return resp

    async def replace(self, registry):
        """ Push triggers a metric collection and pushes all collected metrics
            to the Pushgateway specified by addr
            Note that all previously pushed metrics with the same job and
            instance will be replaced with the metrics pushed by this call.
        """
        with aiohttp.ClientSession(loop=self.loop) as session:
            payload = self.formatter.marshall(registry)
            resp = await session.put(
                self.path, data=payload, headers=self.headers)
        await resp.release()
        return resp

    async def delete(self, registry):
        with aiohttp.ClientSession(loop=self.loop) as session:
            payload = self.formatter.marshall(registry)
            resp = await session.delete(
                self.path, data=payload, headers=self.headers)
        await resp.release()
        return resp
