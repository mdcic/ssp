#!/usr/bin/env python

"""Tools to scan for IPMI devices"""

import logging
import subprocess
import time
import re

from ssp.chassis.netconfig import get_global_to_local_networks_projection, get_all_global_to_local_networks_projection, get_attrset_of_networks
from ssp.chassis.common.scanner import COM_SCANNER
from socket import gethostname,getaddrinfo

HWCONTROLS = [ "IPMIv2_SCANNER" ]
__all__ = HWCONTROLS

LOG = logging.getLogger("ssp.chassis.ipmi.scanner")
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



class IPMIv2_SCANNER(COM_SCANNER):
	"""Represents an generic IPMI device scanner using RMCP protocol."""

	name="IPMIv2_SCANNER"

	@Request_decorator
	def _scan(self, networks={}):
		"""Scan for IPMI devices on restricted set of networks."""
		s = self.__scan_specific_ifaces_by_idiscover(networks)
		s+= self.__scan_specific_ifaces_by_rmcp_ping(networks)
		return s

	@Request_decorator
	def _scan_blindly(self):
		"""Scan for IPMI devices on all networks"""
		s = self.__scan_blindly_by_idiscover()
		s+= self.__scan_blindly_by_rmcp_ping()
		return s

	@Request_decorator
	def __scan_specific_ifaces_by_idiscover(self, networks={}):
		"""Scan for IPMI devices with idiscover on restricted set of networks."""
		s=[]
		if networks.keys():
			for iface in get_attrset_of_networks(networks,'iface_name'):
				s+=self.__idiscover(iface=iface, scantype="RMCP")
				s+=self.__idiscover(iface=iface)
		return s

	@Request_decorator
	def __scan_blindly_by_idiscover(self):
		"""Scan for IPMI devices with idiscover without specifing interfaces"""
		s = self.__idiscover(scantype="RMCP")
		s+= self.__idiscover()
		return s

	@Request_decorator
	def __scan_specific_ifaces_by_rmcp_ping(self, networks={}):
		"""Scan for IPMI devices with rmcp_ping on restricted set of networks."""
		s=[]
		if networks.keys():
			for bcast in get_attrset_of_networks(networks,'iface_broadcast'):
				s+=self.__rmcp_ping(bcast)
		return s

	@Request_decorator
	def __scan_blindly_by_rmcp_ping(self):
		"""Scan for IPMI devices with rmcp_ping without specifing interfaces"""
		return self.__rmcp_ping()

	@Request_decorator
	def __rmcp_ping(self, ip=None):
		"""run rmcp_ping on IP and return list of hosts."""

		myhost=gethostname()
		cmd=["rmcp_ping","-t1"]
		hosts=[]
		if ip:
			cmd.append(ip)
			LOG.debug("scanning " + ip)
		try:
			s = subprocess.Popen(cmd, stderr=open('/dev/null', 'w'), stdout=subprocess.PIPE).communicate()[0]
			for r in re.finditer(r"(?m)^(?P<host>[^\s]+)\s+IPMI$",s):
				h=r.groupdict()
				hip=getaddrinfo(h['host'],623)[0][4][0]
				h['host']=str(hip)
				h['type']='RMCP'
				h['scanner']={'host': myhost, 'scan_ip': ip, 'scanner': 'rmcp_ping', 'scanproto': 'RMCP'}
				hosts.append(h)
			return hosts
		except:
			LOG.error("Cannot run rmcp_ping command.")
			raise


	@Request_decorator
	def __idiscover(self, ip=None, scantype="IPMI", iface=None):
		"""run idiscover on IP and return list of hosts. scantype is 'IPMI' (GetChannelAuthenticationCapabilities) or 'RMCP'"""

		myhost=gethostname()
		cmd=["idiscover","-a"]
		hosts=[]
		if ip:
			cmd.append('-b')
			cmd.append(ip)
			LOG.debug("scanning " + ip)
		if iface:
			cmd.append('-i')
			cmd.append(iface)
			LOG.debug("via " + iface)
		if scantype == "IPMI":
			cmd.append('-g')
		elif scantype == "RMCP":
			pass
		else:
			raise
		try:
			s = subprocess.Popen(cmd, stderr=open('/dev/null', 'w'), stdout=subprocess.PIPE).communicate()[0]
			for r in re.finditer(r"(?m)^[^|]+\|[^|]+\|\s*(?P<host>[^\s|]+)\s*\|.*$",s):
				h=r.groupdict()
				h['type']=scantype
				h['scanner']={'host': myhost, 'iface': iface, 'scanner': 'idiscover', 'scanproto': scantype}
				hosts.append(h)
			return hosts
		except:
			LOG.error("Cannot run idiscover command.")
			raise
