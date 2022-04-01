# -*- coding: utf-8 -*-
import os
from setuptools import setup


setup(
    name="sdirectives",
    description="SimPEG directives - work in progress",
    long_description="SimPEG directives - work in progress",
    author="The emsig community",
    author_email="info@emsig.xyz",
    url="https://emsig.xyz",
    license="Apache-2.0",
    packages=["sdirectives"],
    install_requires=[
        "SimPEG",
        "matplotlib",
    ],
    use_scm_version={
        "root": ".",
        "relative_to": __file__,
        "write_to": os.path.join("sdirectives", "version.py"),
    },
    setup_requires=["setuptools_scm"],
)
