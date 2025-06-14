# coding: utf-8

from setuptools import setup, find_packages

NAME = "metadefender_menlo"
VERSION = "2.0.2"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "aiocontextvars==0.2.2",
    "boto3==1.26.51",
    "certifi==2023.7.22",
    "httpx==0.23.0",
    "kafka-python==2.0.2",
    "python-dotenv==0.19.2",
    "pyyaml==6.0.1",
    "sentry-sdk==1.40.5",
    "tornado==6.3.3",
    "typing==3.7.4.3",
    "urllib3==1.26.18",
    "pytest==8.3.3",
    "pytest-cov==5.0.0",
    "uvicorn==0.34.2",
    "fastapi==0.115.12",
    "python-multipart==0.0.6",
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
