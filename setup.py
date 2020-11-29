"""
This file is used to install this package via the pip tool.
It keeps track of versioning, as well as dependencies and
what versions of python we support.
"""
from setuptools import find_packages, setup


setup(
    name="smartconfig",
    version="0.0.0.dev1",
    description="A smart configuration library.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Python Discord",
    author_email="staff@pythondiscord.com",
    url="https://github.com/python-discord/smartconfig",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 2 - Pre-Alpha",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires='>=3.8',
    include_package_data=True,
    zip_safe=False
)
