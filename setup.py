
import os
import re

from setuptools import find_packages, setup

regexp = re.compile(r'.*__version__ = [\'\"](.*?)[\'\"]', re.S)


init_file = os.path.join(
    os.path.dirname(__file__), 'src', 'aioprometheus', '__init__.py')
with open(init_file, 'rt') as f:  # pylint: disable=unspecified-encoding
    module_content = f.read()
    match = regexp.match(module_content)
    if match:
        version = match.group(1)
    else:
        raise RuntimeError(
            f"Cannot find __version__ in {init_file}")

with open('README.rst', 'rt') as f:  # pylint: disable=unspecified-encoding
    readme = f.read()

def parse_requirements(filename):
    ''' Load requirements from a pip requirements file '''
    with open(filename, 'rt') as fd:  # pylint: disable=unspecified-encoding
        lines = []
        for line in fd:
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line)
    return lines

requirements = parse_requirements('requirements.txt')


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
        extras_require={
            "aiohttp": ["aiohttp>=3.3.2"],
            "binary": ["prometheus-metrics-proto>=18.1.1"],
        },
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: System :: Monitoring"])
