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

"""Tools to scan for SP devices"""

import logging
import time
import re

from ssp.netconfig import get_global_to_local_networks_projection, get_all_global_to_local_networks_projection, get_attrset_of_networks
from socket import gethostname,getaddrinfo

HWCONTROLS = [ "COMMON_SCANNER" ]
__all__ = HWCONTROLS

LOG = logging.getLogger("ssp.chassis.common.scanner")
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



class COM_SCANNER(object):
	"""Represents an skeleton SCANNER class."""

	__host = None
	"""Hostname or IP. Normaly this is broadcast address."""

	__ifaces = None
	"""Local network interface names to use while scanning"""

	__networks = None
	"""Networks to scan"""

	__hostname = None
	"""Hostname of the local host"""

	def __init__(self, host=None, iface=None, networks=None):
		self.__host = host
		self.__ifaces = iface
		self.__networks = networks
		self.__hostname = gethostname()

	@Request_decorator
	def __post_process(self,scanlist=None):
		out={}
		for s in scanlist:
			if s['host'] in out.keys():
				out[s['host']]['proto'].add(s['type'])
				out[s['host']]['scanners'].append(s['scanner'])
			elif s['host'] not in ['[::]','127.0.0.1','0::0']:
				out[s['host']]={'proto':set([s['type']]),'scanners':[s['scanner']]}
		return out

	@Request_decorator
	def scan(self, networks=None):
		"""Scan for SP devices on selected networks only."""
		if networks:
		    scanset=set(networks)
		else:
		    scanset=set(['management'])
		networks_to_scan=get_global_to_local_networks_projection(scanset)
		s=self._scan(networks_to_scan)
		return self.__post_process(s)

	@Request_decorator
	def scan_all(self):
		"""Scan for SP devices on all globaly defined networks."""
		networks_to_scan=get_all_global_to_local_networks_projection()
		s=self._scan(networks_to_scan)
		return self.__post_process(s)

	@Request_decorator
	def scan_blindly(self):
		"""Scan for SP devices on all globaly defined networks."""
		s=self._scan_blindly()
		return self.__post_process(s)
