#!/usr/bin/env python
"""Summary

Attributes:
    VERSION (TYPE): Description
"""
import os
import subprocess
import sys
from distutils.core import setup

from setuptools.command.install import install

from ergo.version import get_version


def from_file(file_name):
    """print long description

    Args:
        file_name (TYPE): Description

    Returns:
        TYPE: Description
    """
    with open(file_name) as f:
        return f.read()


VERSION = get_version()


class VerifyVersionCommandx(install):
    """Custom command to verify that the git tag matches our version

    Attributes:
        description (str): Description
    """
    description = 'verify that the git tag matches our version'

    def run(self):
        """Summary
        """
        tag = os.getenv('CIRCLE_TAG')

        if tag != VERSION:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, VERSION
            )
            sys.exit(info)


class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version

    Attributes:
        description (str): Description
    """
    description = 'verify that the git tag matches our version'

    def run(self):
        """Summary
        """
        tag = os.getenv('CIRCLE_TAG')
        if tag != VERSION:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, VERSION
            )
            sys.exit(info)


setup(
    name='ergo',  # How you named your package folder (MyLib)
    packages=['ergo'],  # Chose the same as "name"
    version=VERSION,  # Start with a small number and increase it with every change you make
    license='MIT',  # Chose a license from here: https://help.github.com/articles/licensing-a-repository
    description='Simple Microservice Development Framework',  # Give a short description about your library
    author='Matthew Hansen',  # Type in your name
    author_email='ergo@mattian.com',  # Type in your E-Mail
    url='https://github.com/nautiluslabsco/ergo',  # Provide either the link to your github or to your website
    download_url=f'https://github.com/nautiluslabsco/ergo/archive/v{VERSION}.tar.gz',  # github release url
    keywords=['execute', 'microservice', 'lambda'],  # Keywords that define your package best
    install_requires=[  # dependencies
        'Click',
        'flask',
        'falcon',
        'ansicolors',
        'click-default-group',
        'pika',
        'pyYaml',
        'mypy_extensions',
        'aio-pika',
        'retry',
        'aiomisc',
        'graphviz',
        'pydash',
        'jsons',
        'quart',
        'kombu',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',  # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Intended Audience :: Developers',  # Define that your audience are developers
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',  # Again, pick a license
        'Programming Language :: Python :: 3',  # Specify which python versions that you want to support
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    long_description=from_file('README.md'),
    long_description_content_type='text/markdown',
    python_requires='>=3',
    entry_points={
        'console_scripts': [
            'ergo=ergo.ergo_click:main'
        ]
    },
    cmdclass={
        'verify': VerifyVersionCommand,
    }
)
