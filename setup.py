# -*- coding: utf-8 -*-
from setuptools import setup
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
DESCRIPTION = open(os.path.join(here, 'DESCRIPTION')).read()

version = '0.0.1'

setup(name='ssp',
      version=version,
      description="System Service Processor communication library",
      long_description=DESCRIPTION,
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Operating System :: POSIX :: Linux',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: System :: Systems Administration',
      ],
      author='Yury Konovalov',
      author_email='YKonovalov@gmail.com',
      url='https://github.com/YKonovalov/ssp',
      license='GPLv3+',
      packages=['ssp'],
      scripts=['tools/ssp-chassis-scanner'],
      include_package_data=True,
      install_requires=[
          'pywbem',
          'paramiko'
      ]
)
