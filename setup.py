"""Setup for inspector."""
import os
from setuptools import setup

from aker import __author__, __author_email__, __license__, __version__


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='aker',
    version=__version__,
    description='Aker SSH Gateway',
    long_description=read('README.md'),
    url='http://github.com/aker-gateway/Aker',
    author=__author__,
    author_email=__author_email__,
    license=__license__,
    packages=['aker'],
    install_requires=['configparser', 'urwid', 'paramiko'],
    zip_safe=False,
    entry_points={'console_scripts': ['aker = aker.aker:main']}
)
