# Copyright (C) 2012-2013  Yury Konovalov <YKonovalov@gmail.com>
#
# This file is part of sspy.
#
# sspy is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# sspy is distrubuted in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with sspy; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

"""
I{sspy} (a System Service Processor Python communication library)
is a module for python 2.6 or greater that implements a set of operation with
common service processors. It targets a number of applied fields ranging from
HA clustering (fencing agents) to C{HPC} and datacenter management systems -
anywere where there is a need to effectively control computer systems remotely.

There are four high-level functionalyty in the library:
 -discovery SP on the network: L{Scanner},
 -probbing for SP type: L{Identify},
 -collecting vital SP and system(s) data: L{ServiceProcessor},
 -issuing commands to specific SP: L{ServiceProcessor}.

sspy is written in python, but uses some command-line tools, like ipmitool and
is released under the GNU Lesser General Public License (LGPL).

Website: U{https://github.com/YKonovalov/sspy/}
"""

import sys

if sys.version_info < (2, 6):
    raise RuntimeError('You need python 2.6 for this module.')


__author__ = "Yury Konovalov <YKonovalov@gmail.com>"
__version__ = "0.0.1"
__license__ = "GNU General Public License (GPL)"


from service_processor import ServiceProcessor
from scanner import Scanner

__all__ = [ 'ServiceProcessor',
            'Scanner' ]
