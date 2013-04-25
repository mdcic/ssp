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

"""Gives a facility to identify type of the Service Processor"""

import logging
import subprocess
import time
import sys,os,re
import httplib

__all__ = [ "IDENT" ]
LOG = logging.getLogger("ssp.ident")

__MAC_TABLE_FILE="/home/yurix/eucalyptus/common/c2/hw/chassis/nmap-mac-prefixes"

defaults={	'DELL-iDRAC6':{'user':'root','pass':'calvin'},
		'IBM-BLADECENTER':{'user':'USERID','pass':'PASSW0RD'},
		'IBM-RSA':{'user':'USERID','pass':'PASSW0RD'},
		'HP-iLO':{'user':'Administrator','pass':None}}

def Request_decorator(func):
	"""Logs all requests."""

	def decorator(self, *args, **kwargs):
		if kwargs:
			LOG.info("%s(%s)%s called.", func.func_name, args, kwargs)
		else:
			LOG.info("%s(%s) called.", func.func_name, args)

		return func(self, *args, **kwargs)

	return decorator


@Request_decorator
def ping(ip):
	"""Ping ip and return True if alive."""
	try:
		if subprocess.call(["ping","-c1","-w1", "-nrq", ip], stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT):
			return None
		else:
			return True
	except:
		LOG.error("Cannot run ping command.")
		raise


@Request_decorator
def mac_by_ip(ip):
	"""Lookup mac via arp table after ping request."""
	
	if ping(ip):
		s = subprocess.Popen(["arp","-n", ip], stderr=open('/dev/null', 'w'), stdout=subprocess.PIPE).communicate()[0]
		mac = re.search(r"(?m)^" + ip + r"\s+ether\s+([a-f0-9:]{17}).*$", s)
		if mac:
			return mac.group(1)


@Request_decorator
def macpreffix(mac):
	"""Return preffix of a given mac."""
	if mac:
	    return mac.replace(":", "")[:6].upper()


@Request_decorator
def vendor_by_mac(mac):
	"""Lookup mac via nmap-mac-prefixes table to guess SP vendor."""
	
	
	try:
		fd = open( __MAC_TABLE_FILE, 'r' )
	except:
		LOG.error("Cannot open mac table at %s .",
			__MAC_TABLE_FILE)
		raise
	
	data = fd.read()
	vendor = re.search(r"(?m)^" + macpreffix(mac) + r" (.*)$", data)
	if vendor:
		vendor=vendor.group(1)
	return vendor


@Request_decorator
def vendor_by_ip(ip):
	"""Return array of strings with guessed SP types."""
	
	mac = mac_by_ip(ip)
	if mac:
		return vendor_by_mac(mac)


@Request_decorator
def guess_sptype_by_ip(ip):
	"""Return string array with possible SP types."""
	
	vendor=vendor_by_ip(ip)
	if vendor in ("Dell","Dell Inc.","Dell Computer"):
		return ("DELL-iDRAC6","DELL-CMC")
	if vendor in ("IBM","IBM Japan, Fujisawa Mt+d"):
		return ("IBM-RSA","IBM-BLADECENTER")
	if vendor in ("Hewlett Packard","Hewlett-Packard Company"):
		return ("HP-iLO2")


@Request_decorator
def guess_sptype_by_http(ip):
	"""Return array of strings with guessed SP types."""
	try:
		conn = httplib.HTTPConnection(ip)
		conn.request("GET", "/")
		r1 = conn.getresponse()
		location = r1.getheader('location')
		doc = r1.read()
		conn.close()
	except:
		return None
	if location:
		if re.match(r"https://" + ip + "/start.html",location):
			return ("DELL-iDRAC6")
		if re.match(r"http://" + ip + "/private/main.php",location):
			return ("IBM-BLADECENTER")
		if re.match(r"http://" + ip + "/private/testcookie.ssi",location):
			return ("IBM-RSA")
		if re.match(r"https://" + ip + ":443/",location):
			try:
				conns = httplib.HTTPSConnection(ip)
				conns.request("GET", "/")
				r2 = conns.getresponse()
				locations = r2.getheader('location')
				conns.close()
				if locations:
					if re.match(r"https://" + ip + ":443//cgi-bin/webcgi/index",locations):
						return ("DELL-CMC")
			except:
				pass
	if doc:
		if re.search(r"HP Integrated Lights-Out 2",doc):
			return ("HP-iLO2")
	#print r1.getheaders()
	#print doc


@Request_decorator
def guess_sptype_by_probeall(ip):
	"""Return array of strings with guessed SP types."""
	
	vendor=vendor_by_ip(ip)
	if vendor in ("Dell","Dell Inc."):
		guessed_sptype = "DELL"


@Request_decorator
def suggest_sptype(ip):
	"""Guess SP type by probbing http or mac preffix."""
	
	sptype = guess_sptype_by_http(ip)
	if not sptype:
		sptype = guess_sptype_by_ip(ip)
	if sptype:
		return sptype
