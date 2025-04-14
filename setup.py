#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = f.read().splitlines()

setup(
    name="webscraper-gui",
    version="0.1.0",
    author="Developer",
    author_email="developer@example.com",
    description="A web scraper application with GUI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/webscraper-gui",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'webscraper-gui=main:main',
        ],
    },
)