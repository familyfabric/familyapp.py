#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup

requirements = []
with open('requirements.txt') as f:
  requirements = f.read().splitlines()

setup(name='familyapp.py',
      author='Piotr Giedziun',
      version='0.0.10',
      packages=['familyapp',],
      license='MIT',
      author_email='piotrgiedziun@gmail.com',
      url='https://github.com/piotrgiedziun/familyapp.py',
      description='A python wrapper for the FamilyApp API',
      install_requires=requirements,
)