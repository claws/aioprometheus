
import os
import re

from pip.req import parse_requirements
from pip.download import PipSession
from setuptools import setup, find_packages


regexp = re.compile(r'.*__version__ = [\'\"](.*?)[\'\"]', re.S)


init_file = os.path.join(
    os.path.dirname(__file__), 'src', 'aioprometheus', '__init__.py')
with open(init_file, 'r') as f:
    module_content = f.read()
    match = regexp.match(module_content)
    if match:
        version = match.group(1)
    else:
        raise RuntimeError(
            'Cannot find __version__ in {}'.format(init_file))

with open('README.rst', 'r') as f:
    readme = f.read()

with open('requirements.txt', 'r') as f:
    requirements = [line for line in f.read().split('\n') if len(line.strip())]


if __name__ == "__main__":

    setup(
        name="aioprometheus",
        version=version,
        author="Chris Laws",
        author_email="clawsicus@gmail.com",
        description="A Prometheus Python client library for asyncio-based applications",
        long_description=readme,
        license="MIT",
        keywords=["prometheus", "monitoring", "metrics"],
        url="https://github.com/claws/aioprometheus",
        package_dir={'': 'src'},
        packages=find_packages('src'),
        install_requires=requirements,
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3.6",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: System :: Monitoring"])
