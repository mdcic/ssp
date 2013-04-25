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
from ssp.chassis.common.scanner import COM_SCANNER
from socket import gethostname,getaddrinfo

HWCONTROLS = [ "WBEM_SCANNER" ]
__all__ = HWCONTROLS

LOG = logging.getLogger("ssp.chassis.wbem.scanner")
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



class WBEM_SCANNER(COM_SCANNER):
	"""Represents an generic WBEM device scanner using SLP protocol."""

	name="WBEM_SCANNER"
	
	scanspec=[('SLP' ,'service:service-agent'),
		  ('WBEM','service:wbem')]
	""" Scan for specific service in form <TAG>,<SLP service name>
	    example: [('IBMBC','service:management-hardware.IBM:management-module')]"""

	@Request_decorator
	def _scan(self, networks={}):
		"""Scan for IPMI devices on restricted set of networks."""
		s = self.__scan_specific_ifaces_by_slptool(networks)
		return s

	@Request_decorator
	def _scan_blindly(self):
		"""Scan for IPMI devices on all networks"""
		s = self.__scan_blindly_by_slptool()
		return s

	@Request_decorator
	def __scan_specific_ifaces_by_slptool(self, networks={}):
		"""Scan for SLP devices with rmcp_ping on restricted set of networks."""
		if_ips=set()
		if networks.keys():
			for ifip in get_attrset_of_networks(networks,'iface_ip_and_preffix'):
				if_ips.add(ifip.split('/')[0])
		ifspec=",".join(if_ips)
		s = self.__slptool(ifs=ifspec)
		return s

	@Request_decorator
	def __scan_blindly_by_slptool(self):
		"""Scan for IPMI devices with rmcp_ping without specifing interfaces"""
		s = self.__slptool()
		return s

	@Request_decorator
	def __slptool(self, ifs=None, scantype="SLP"):
		"""Run slptool on IP and return list of hosts. scantype is 'WBEM' or 'SLP'
		   slptool can restrict """

		hosts=[]
		myhost=gethostname()

		icmd=["slptool"]
		if ifs:
			icmd.append("-i")
			icmd.append(ifs)
			LOG.debug("scanning via " + ifs)
		icmd.append("findsrvs")

		for scantype,scanservice in self.scanspec:
			cmd=list(icmd)
			cmd.append(scanservice)
			LOG.debug(str(cmd))
			try:
				s = subprocess.Popen(cmd, stderr=open('/dev/null', 'w'), stdout=subprocess.PIPE).communicate()[0]
				print str(s)
				for r in re.finditer(r"(?m)^.*//(?P<host>[^\s/,]+),+.*$",s):
					h=r.groupdict()
					h['type']=scantype
					h['scanner']={'host': myhost, 'iface_ip': ifs, 'scanner': 'slptool', 'scanproto': scantype}
					hosts.append(h)
			except:
				LOG.error("Cannot run slptool command.")
				raise
		return hosts
