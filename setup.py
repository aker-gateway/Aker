# -*- coding: utf-8 -*-
"""Setup file for Aker"""

import os

from setuptools import find_packages, setup


def __path(filename):
    return os.path.join(os.path.dirname(__file__), filename)

with open(__path('requirements.txt')) as f:
    REQUIRES = [l.strip() for l in f.readlines()]

VERSION = '0.5.0'

setup(
    name='aker',
    packages=find_packages(exclude=('tests',)),
    install_requires=REQUIRES,
    version=VERSION,
    description='Aker SSH gateway',
    author='Ahmed Nazmy',
    author_email='ahmed@nazmy.io',
    url='https://github.com/aker-gateway/Aker',
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'aker = aker.cli.aker:run',
            'akerctl = aker.cli.akerctl:run',
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 2',  # :(
        'Operating System :: OS Independent',
    ],
)
