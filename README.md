SSP
===
System Service Processor communication library is a module for python that
implements a set of operation with common system's service processors. It
can be used in various areas from HA clustering (fencing agents) to HPC
and datacenter management systems. E.g. where there is a need to control
computer systems remotely. There are four major functions:
* discovery SP on the network,
* probbing for SP type,
* collecting vital SP and system(s) data,
* issuing commands to specific SP.

Includes tools to remotly control servers service processors such as:
* DELL iDRAC6,
* IBM BladeCenter,
* IBM IMM,
* IBM RSA,
* HP iLO

Requirements
------------

  - python
  - pywbem
  - paramiko

Get source
----------

::

  git clone git://github.com/mdcic/ssp
  cd ssp

Install
-------
You can build and install sspy with setuptools:

::

    python setup.py install

Or build RPM package:

::

    make srpm
    mock {src.rpm file}

Portability
-----------

This library tested on Linux. Should work on UNIXes as well once
you'll have all dependancies in place.

More info
---------

Please file bug reports at https://github.com/mdcic/ssp

**License**: GPLv3+
Copyright © 2013  Yury Konovalov <YKonovalov@gmail.com>
