from setuptools import setup, find_packages
import uuid

setup(
    name=f'component_{uuid.uuid1()}',
    packages=find_packages(include=['*']),
    install_requires=[
        'ergo'
    ]
)
