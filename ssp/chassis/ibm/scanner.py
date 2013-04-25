#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2012-2013  Yury Konovalov <YKonovalov@gmail.com>
#
# This file is part of SSP.
#
# SSP is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SSP is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SSP.  If not, see <http://www.gnu.org/licenses/>.

"""Tools to scan for WBEM devices"""

import logging
import subprocess
import time
import re

from ssp.chassis.netconfig import get_global_to_local_networks_projection, get_all_global_to_local_networks_projection, get_attrset_of_networks
from ssp.chassis.wbem.scanner import WBEM_SCANNER
from ssp.chassis.common.scanner import COM_SCANNER
from socket import gethostname,getaddrinfo

HWCONTROLS = [ "IBM_SCANNER" ]
__all__ = HWCONTROLS

LOG = logging.getLogger("ssp.chassis.ibm.scanner")
LOG.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
LOG.addHandler(ch)


def Request_decorator(func):
	"""Logs all requests."""

	def decorator(self, *args, **kwargs):
		if kwargs:
			LOG.info("%s(%s)%s called.", func.func_name, args, kwargs)
		else:
			LOG.info("%s(%s) called.", func.func_name, args)

		return func(self, *args, **kwargs)

	return decorator



class IBM_SCANNER(WBEM_SCANNER,COM_SCANNER):
	"""Represents an generic WBEM device scanner using SLP protocol."""
	name="IBM_SCANNER"
	scanspec=[('IBM-AMM','service:management-hardware.IBM:management-module'),
		  ('IBM-CM','service:management-hardware.IBM:chassis-management-module'),
		  ('IBM-IMM' , 'service:management-hardware.IBM:integrated-management-module'),
		  ('IBM-IMM2', 'service:management-hardware.IBM:integrated-management-module2'),
		  ('IBM-CEC', 'service:management-hardware.IBM:cec-service-processor')
		]
