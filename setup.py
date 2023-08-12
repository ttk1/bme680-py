#!/bin/env python

from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()

with open("LICENSE") as f:
    license = f.read()

setup(
    name="bme680",
    version="1.0.0",
    description="Python library for BME680 sensor",
    long_description=readme,
    author="tama@ttk1",
    author_email="tama@ttk1.net",
    url="https://github.com/ttk1/bme680-py",
    license=license,
    packages=find_packages(exclude=("test",)),
)
