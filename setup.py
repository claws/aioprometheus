
from pip.req import parse_requirements
from pip.download import PipSession
from setuptools import setup


install_reqs = parse_requirements("requirements.txt", session=PipSession())
requires = [str(ir.req) for ir in install_reqs]


if __name__ == "__main__":

    setup(
        name="aioprometheus",
        version="0.0.1",
        author="Chris Laws",
        author_email="clawsicus@gmail.com",
        description="A Prometheus Python client library for asyncio-based applications",
        long_description="",
        license="MIT License",
        keywords=["prometheus", "monitoring", "metrics"],
        url="https://github.com/claws/aioprometheus",
        packages=["aioprometheus"],
        install_requires=requires,
        pyrobuf_modules="proto",
        test_suite="tests",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: Apache Software License",
            "Natural Language :: English",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3.5",
            "Topic :: System :: Monitoring"])
