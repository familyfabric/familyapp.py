from setuptools import setup

requirements = []
with open('requirements.txt') as f:
  requirements = f.read().splitlines()

setup(name='familyapp.py',
      author='Piotr Giedziun',
      version='0.0.1',
      packages=['familyapp',],
      license='MIT',
      url='https://github.com/piotrgiedziun/familyapp.py',
      description='A python wrapper for the FamilyApp API',
      install_requires=requirements,
)