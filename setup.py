#!/usr/bin/env python
import os
from setuptools import setup, find_packages

__version__ = "1.8.2"
__repo__ = "https://github.com/ateliedocodigo/py-queue-manager"


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="py-queue-manager",
    version=__version__,
    description="Library to deal with RabbitMQ",
    long_description=read("README.rst"),
    author="Luis Fernando Gomes",
    author_email="luiscoms@ateliedocodigo.com.br",
    url=__repo__,
    download_url="{}/tarball/{}".format(__repo__, __version__),
    packages=find_packages(exclude=["tests", "tests.*"]),
    zip_safe=False,
    include_package_data=True,
    license="MIT",
    platforms="any",
    install_requires=["pika>=1"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
    ]
)
