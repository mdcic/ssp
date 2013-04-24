#!/usr/bin/env python

"""Gives a facility to control DELL iDRAC6 system"""

import logging
import subprocess
import time
import re

#import c2.mongodb

from ssp.remote.ssh import SSHchannel

HWCONTROLS = [ "DELLiDRAC6" ]
__all__ = HWCONTROLS

LOG = logging.getLogger("ssp.chassis.dell.idrac6")


def Request_decorator(func):
	"""Logs all requests."""

	def decorator(self, *args, **kwargs):
		if kwargs:
			LOG.info("%s(%s)%s called.", func.func_name, args, kwargs)
		else:
			LOG.info("%s(%s) called.", func.func_name, args)

		return func(self, *args, **kwargs)

	return decorator


class DELLiDRAC6:
	"""Represents an DELL iDRAC service controller."""

	__host = None
	"""iDRAC host name or IP."""

	__user = None
	"""User name for logging in on iDRAC."""

	__password = None
	"""Password for logging in on iDRAC."""

	__sshpubkey = None
	"""Key to install into iDRAC."""

	__sshprivkey = None
	"""Key to use for SSH connection to iDRAC."""

	__sshpipe = None
	"""SSH client object for sending commands to iDRAC."""


	def __init__(self, host):
		self.__host = host

		#chassis = c2.mongodb.collection("hw.chassises").find_one({ "_id": self.__host })
		chassis = None
		#c2.mongodb.collection("hw.chassises").find_one({ "_id": self.__host })
		if not chassis:
			raise Error("Chassis {0} is not registered.", self.__host)

		self.__user = chassis["user"]
		self.__password = chassis["password"]
		self.__sshpipe = SSHchannel(self.__host, user=self.__user, sshkey=self.__sshprivkey)

	def __init__(self, host, user, password):
		self.__host = host
		self.__user = user
		self.__password = password
		self.__sshpipe = SSHchannel(self.__host, user=self.__user, password=self.__password)

	@Request_decorator
	def connect(self):
		"""Connect to iDRAC."""
		return self.__sshpipe.connect()

	@Request_decorator
	def disconnect(self):
		"""Disconnect from iDRAC."""
		return self.__sshpipe.disconnect()


	@Request_decorator
	def powerstate(self):
		"""Returns power state of the system."""

		reply_info={	'on':	("on", "powering on", "powering off"),
				'off':	("off")}
		return self.__sshpipe.smartcommand("racadm serveraction powerstatus", 
			r"(?imu)(ON|OFF|Powering ON|Powering OFF)\s*$",
			reply_info)


	@Request_decorator
	def alive(self):
		"""Returns True if system is powered on."""

		state=self.powerstate()
		if state == 'on':  return True
		if state == 'off': return False
		return None


	@Request_decorator
	def poweron(self):
		"""Power On the system."""

		return self.__sshpipe.simplecommand("racadm serveraction powerup", 
			r"(?imu)(Server power operation successful|Server is already powered ON).*\s*$")


	@Request_decorator
	def poweroff(self):
		"""Power Off the system."""

		return self.__sshpipe.simplecommand("racadm serveraction powerdown", 
			r"(?imu)(Server power operation successful|Server is already powered OFF).*\s*$")

	@Request_decorator
	def powercycle(self):
		"""Power cycle the system."""

		return self.__sshpipe.simplecommand("racadm serveraction powercycle", 
			r"(?imu)(Server power operation successful).*\s*$")


	@Request_decorator
	def reset(self):
		"""Reset the system."""

		return self.__sshpipe.simplecommand("racadm serveraction hardreset", 
			r"(?imu)(Server power operation successful).*\s*$")


	@Request_decorator
	def setpxeboot(self):
		"""Set boot device to PXE for the system."""

		pxe = self.__sshpipe.simplecommand("racadm config -g cfgServerInfo -o cfgServerFirstBootDevice PXE", 
			r"(?imu)(Object value modified successfully).*\s*$")
		once = self.__sshpipe.simplecommand("racadm config -g cfgServerInfo -o cfgServerBootOnce 0", 
			r"(?imu)(Object value modified successfully).*\s*$")
		return	pxe and once

	@Request_decorator
	def getpxeboot(self):
		"""Returns True if boot device set to PXE."""

		return self.__sshpipe.simplecommand("racadm getconfig -g cfgServerInfo", 
			r"(?im).*(cfgServerFirstBootDevice=PXE).*")


	@Request_decorator
	def getvpd(self):
		"""Returns SP and systems VPD data."""

		sysinfo = self.__sshpipe.command("racadm getsysinfo")
		spinfo = self.__sshpipe.command("racadm getconfig -g idRacInfo")
		spxinfo = self.__sshpipe.command("show hdwr1/chassis1")
		system={'macs':{}, 'sn':'', 'model':'', 'power':'' }
		vpd={	'sp':	{'uuid':'', 'mac':'', 'name':'', 'ip':'', 'version':'', 'product':'', 'model':''},
			'sys':	{}}

		# SP attributes
		res = re.search(r"(?m)^MAC Address\s+=\s+([a-f0-9:]{17}$)", sysinfo)
		if res:
			sp_mac=res.group(1)
			vpd['sp']['mac']=sp_mac

		res = re.search(r"(?m)^DNS RAC Name\s+=\s+([A-Za-z0-9-]+)$", sysinfo)
		if res:
			sp_name=res.group(1)
			vpd['sp']['name']=sp_name

		res = re.search(r"(?m)^Firmware Version\s+=\s+([0-9.]+)$", sysinfo)
		if res:
			sp_ver=res.group(1)
			vpd['sp']['version']=sp_ver

		res = re.search(r"(?m)^Current IP Address\s+=\s+([0-9.]+)$", sysinfo)
		if res:
			sp_ip=res.group(1)
			vpd['sp']['ip']=sp_ip

		res = re.search(r"(?m)^# idRacProductInfo\s*=\s*([A-Za-z0-9.-_ ]+)$", spinfo)
		if res:
			sp_prod = res.group(1)
			vpd['sp']['product']=sp_prod

		res = re.search(r"(?m)^# idRacName\s*=\s*([A-Za-z0-9]+)$", spinfo)
		if res:
			sp_model = res.group(1)
			vpd['sp']['model']=sp_model

		res = re.search(r"(?m)^# idRacType\s*=\s*([0-9]+)$", spinfo)
		if res:
			sp_subtype = res.group(1)
			vpd['sp']['subtype']=sp_subtype

		# SYSTEM attributes
		res = re.search(r"(?m)^\s+PlatformGUID\s+=\s+([A-Za-z0-9-]+)$", spxinfo)
		if res:
			sys_uuid=res.group(1).replace("-", "").upper()
			vpd['sys'][sys_uuid]=system
			# iDRAC share uuid between chassis and system
			vpd['sp']['uuid']=sys_uuid

		for res in re.finditer(r"(?m)^NIC(?P<id>[0-9]+) Ethernet\s+=\s+(?P<mac>[a-f0-9:]{17}$)",sysinfo):
			iface = res.groupdict()
			eth_index = str(int(iface['id']) - 1)
			vpd['sys'][sys_uuid]['macs'][eth_index] = iface['mac']

		res = re.search(r"(?m)^System Model\s+=\s+([A-Za-z0-9.-_ ]+)$", sysinfo)
		if res != None:
			sys_model=res.group(1)
			vpd['sys'][sys_uuid]['model']=sys_model
		else:
			ok_flag = False

		res = re.search(r"(?m)^Service Tag\s+=\s+([A-Za-z0-9]+)$", sysinfo)
		if res:
			sys_sn=res.group(1)
			vpd['sys'][sys_uuid]['sn']=sys_sn

		res = re.search(r"(?m)^Power Status\s+=\s+.*(ON|OFF)$", sysinfo)
		if res:
			sys_power=res.group(1)
			vpd['sys'][sys_uuid]['power']=sys_power

		return vpd

