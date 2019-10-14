#!/usr/bin/env python
import os
import sys

from distutils.core import setup
from setuptools.command.install import install
import subprocess

def from_file(file_name):
  """print long description"""
  with open(file_name) as f:
    return f.read()

VERSION = from_file('VERSION').strip()

class VerifyVersionCommandx(install):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = os.getenv('CIRCLE_TAG')

        if tag != VERSION:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, VERSION
            )
            sys.exit(info)

class VerifyVersionCommand(install):
  """Custom command to verify that the git tag matches our version"""
  description = 'verify that the git tag matches our version'

  def run(self):
    tag = os.getenv('CIRCLE_TAG')
    if tag != VERSION:
      info = "Git tag: {0} does not match the version of this app: {1}".format(
        tag, VERSION
      )
      sys.exit(info)


setup(
  name = 'ergo', # How you named your package folder (MyLib)
  packages = ['src'], # Chose the same as "name"
  version = VERSION, # Start with a small number and increase it with every change you make
  license = 'MIT', # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'Exo Runtime Gamut Orchestration', # Give a short description about your library
  author = 'Matthew Hansen', # Type in your name
  author_email = 'ergo@mattian.com', # Type in your E-Mail
  url = 'https://github.com/mattian7741/ergo', # Provide either the link to your github or to your website
  download_url = f'https://github.com/mattian7741/ergo/archive/v{VERSION}.tar.gz', # github release url
  keywords = ['execute', 'microservice', 'lambda'], # Keywords that define your package best
  install_requires = [ # dependencies
    'Click',
    'flask',
    'falcon',
  ],
  classifiers = [
    'Development Status :: 3 - Alpha', # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers', # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License', # Again, pick a license
    'Programming Language :: Python :: 3', #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
  ],
  long_description = from_file('README.md'),
  long_description_content_type = 'text/markdown',
  python_requires = '>=3',
  entry_points = {
    'console_scripts': [
      'ergo=src.cli:main'
    ]
  },
  cmdclass = {
    'verify': VerifyVersionCommand,
  }
)

