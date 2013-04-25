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

"""Gives a facility to identify local node configuration"""

import logging
import subprocess
import time
import sys,os,re
import array
from IPy import IP

__all__ = [ "NETCONFIG" ]
LOG = logging.getLogger("ssp.netconfig")

__NETWORKS={'cluster'	:{'ipv4':'192.168.50.0/24'},
	    'management':{'ipv4':'172.24.8.0/23'},
	    'storage'	:{'ipv4':'192.168.50.0/24'},
	    'vnetwork'	:{'ipv4':'172.24.0.0/24'},
	    'croc-main'	:{'ipv4':'172.25.6.0/24'},
	    'croc-test'	:{'ipv4':'172.24.8.0/23'}}

__SPECIAL_IPV4={'slp-multicast':	{'ipv4':'239.255.255.253',	'type': 'multicast'},
		'ipmi-broadcast':	{'ipv4':'255.255.255.255',	'type': 'broadcast'},
		'upnp-multicast':	{'ipv4':'239.255.255.250',	'type': 'multicast'},
		'ganglia-multicast':	{'ipv4':'239.2.11.71',		'type': 'multicast'}}

def Request_decorator(func):
	"""Logs all requests."""

	def decorator(self, *args, **kwargs):
		if kwargs:
			LOG.info("%s(%s)%s called.", func.func_name, args, kwargs)
		else:
			LOG.info("%s(%s) called.", func.func_name, args)

		return func(self, *args, **kwargs)

	return decorator

def get_attrset_of_networks(networks={}, attr='iface_name'):
	"""Return a set() of specific attribute composed of the specified networks."""
	attrs=set()
	for net in networks.keys():
		for nettype in networks[net].keys():
			if attr in networks[net][nettype].keys():
				attrs.add(networks[net][nettype][attr])
	return attrs

def get_ifaces():
	"""Return a list of all local configured interfaces."""
	ifaces=set()
	try:
		s = subprocess.Popen(["ip","r","s","scope","link"], stderr=open('/dev/null', 'w'), stdout=subprocess.PIPE).communicate()[0]
		for r in re.finditer(r"(?m)^.*\s+dev\s+(?P<iface>[^\s]+).*$",s):
			ifaces.add(r.groupdict()['iface'])
		return ifaces
	except:
		LOG.error("Cannot run ping command.")
		raise

def get_iface_by_route(ip):
	"""Return the local interface name for specific IP address. None for indirectly routed addresses"""
	try:
		s = subprocess.Popen(["ip","r","g",ip], stderr=open('/dev/null', 'w'), stdout=subprocess.PIPE).communicate()[0]
		for r in re.finditer(r"(?m)^"+ip+"\s+dev\s+(?P<iface>[^\s]+).*$",s):
			return r.groupdict()['iface']
	except:
		LOG.error("Cannot run 'ip r g' command.")
		raise

def check_actual_iface(network, iface):
	"""Return the local interface IP/prefix and broadcast address for specific network."""
	net=network.net()
	brd=str(network.broadcast())
	try:
		s = subprocess.Popen(["ip","a","s","dev",iface], stderr=open('/dev/null', 'w'), stdout=subprocess.PIPE).communicate()[0]
		for r in re.finditer(r"(?m)^\s+inet\s+(?P<net>[^\s]+)\s+brd\s+(?P<brd>[^\s]+).*$",s):
			n=r.groupdict()
			localif=IP(n['net'],make_net=True)
			if localif.net() == net:
				if n['brd'] != brd:
					LOG.error("Interface (%s) should have broadcast (%s), but set to (%s).",iface, brd, n['brd'])
				return n['net'],n['brd']
			elif network[1] in localif:
				LOG.error("Interface (%s) configured incorrectly. Preffix on net (%s) is set to (%s).",iface, net, localif)
				return n['net'],n['brd']
		LOG.error("Broadcast is not set on interface (%s) or this is a bug. Direct route for (%s) exists, but I can't find this network with broadcast (%s).",iface, str(net), brd)
		return None,None
	except:
		LOG.error("Cannot run 'ip a s dev' command.")
		raise

def get_all_global_to_local_networks_projection():
	"""Returns dict of all defined global networks as they seen on local host (if any). Return an empty dict if none is actually configured"""
	return get_global_to_local_networks_projection(set(__NETWORKS.keys()))

def get_global_to_local_networks_projection(networkset=set()):
	"""Returns dict of specified networks as they seen on local host (if any). Return an empty dict if none of specified networks is actually configured"""
	networks={}
	for name in networkset.intersection(__NETWORKS.keys()):
		networks[name]={}
		for nettype in __NETWORKS[name].keys():
			net=__NETWORKS[name][nettype]
			try:
				IPnet=IP(net)
				first=str(IPnet[1])
				broadcast=str(IPnet.broadcast())
				version=str(IPnet.version())
			except:
				LOG.error("Wrong configuration. Bad network: %s", str(net))
				continue
			iface=get_iface_by_route(first)
			if iface:
				v='IPv'+version
				networks[name][v]={}
				# Should be part of the dict
				networks[name][v]['net']=net
				networks[name][v]['broadcast']=broadcast
				networks[name][v]['firstIP']=first
				# Actual configuration part of the dict
				networks[name][v]['iface_name']=iface
				networks[name][v]['iface_ip_and_preffix'],networks[name][v]['iface_broadcast']=check_actual_iface(IPnet,iface)
			else:
				del networks[name]
	return networks
