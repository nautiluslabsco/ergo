import uuid

from setuptools import find_packages, setup

setup(
    name=f'component_{uuid.uuid1()}',
    packages=find_packages(include=['*']),
    install_requires=[
        'ergo'
    ]
)
