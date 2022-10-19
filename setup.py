# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "metadefender_menlo"
VERSION = "1.3.4"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "flask>=1.1.2",
    "urllib3>=1.25.9"
]

setup(
    name=NAME,
    version=VERSION,
    description="MetaDefender - Menlo Security Integration",
    author_email="",
    url="",
    keywords=["MetaDefender", "Menlo Security", "Sanitization", "File Scan"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_dir={NAME: 'metadefender_menlo'},
    include_package_data=False,
    entry_points={
        'console_scripts': ['release=__main__:main']},
    long_description="""\
    This document outlines the required processing flow and API for a service implementing the Menlo REST API. This configurable interface will allow the MSIP to provide a file to an externally controlled API implementing the following defined interface. The primary purpose of this integration is to submit a file to the external API for additional file processing. The external API can then process the file and make the outcome available to the MSIP. Along with sending the file, MSIP will also be able to send specific metadata that can be used for auditing or as part of the analysis process
    """
)
