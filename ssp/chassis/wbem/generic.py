#!/usr/bin/env python

"""Gives a facility to control Service Processors via WBEM"""

import logging
import subprocess
import time
import re

from pywbem import WBEMConnection
from pywbem import CIMInstanceName
from pywbem import CIMClassName
from pywbem import CIMDateTime
from datetime import datetime
from pprint import pprint as pp

from ssp.remote.ssh import SSHchannel
import ssp.chassis.wbem.common as WBEMC


HWCONTROLS = [ "WBEM" ]
HWCONTROLS_DESCRIPTION  = [ "Web-Based Enterprise Management (WBEM)" ]
HWCONTROLS_STANDARD_URL = [ "http://www.dmtf.org/standards/wbem" ]

VERSIONS_TESTED = [ "1.0"]
VERSIONS_SUPPORTED = [ "1.0", "2.0"]

__all__ = HWCONTROLS

LOG = logging.getLogger("ssp.chassis.wbem.v2")

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


class WBEM:
	"""Represents an service controller with support for Web-Based Enterprise Management (WBEM)."""

	__host = None
	"""SP host name or IP."""

	__user = None
	"""User name for logging in on SP."""

	__password = None
	"""Password for logging in on SP."""

	__port = None
	"""SP port number of WBEM service."""
	
	__proto = None
	"""SP protocol to use 'http' or 'https'. Default 'http'."""

	__namespace = None
	"""SP WBEM namespace to use. Default 'root/cimv2'."""

	__url = None
	"""SP WBEM URL. Combined as proto://user:passwdord@host:port:namespase by init()."""


	__wbempipe = None
	"""SP WBEM connection object to send commands to."""

	def __init__(self, host=None, user=None, password=None, port=None, proto='http', namespace='root/cimv2'):
		self.__host = host
		self.__user = user
		self.__password = password
		self.__proto = proto
		self.__namespace = namespace

		if self.__user is not None or self.__password is not None:
			creds = (self.__user, self.__password)
		if self.__host is not None:
			self.__url = '%s://%s' % (self.__proto, self.__host)
			if port is not None:
            			self.__url += ':%d' % port 
			
			self.__wbempipe = WBEMConnection(self.__url, creds, default_namespace = self.__namespace)

	@Request_decorator
	def connect(self):
		"""Connect to WBEM."""

		for comp in self.__wbempipe.EnumerateInstances('CIM_ComputerSystem'):
			LOG.debug("CIM_ComputerSystem '%s", comp.items())
			for dedication in comp['Dedicated']:
				if dedication in [ WBEMC.ChassisManager, WBEMC.ManagementController ]:
					return True
		return False

	@Request_decorator
	def disconnect(self):
		"""Disconnect from WBEM."""
		return True


	@Request_decorator
	def powerstate(self):
		"""Returns power state of the system."""

		reply_info={	'on':	("on", "powering on", "powering off"),
				'off':	("off")}
		return self.__wbempipe.smartcommand("racadm serveraction powerstatus", 
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
	def getpxeboot(self, sp_system_id=None):
		"""Returns True if boot device set to PXE."""

		bootlists = self.getbootlists(sp_system_id)
		for listname in bootlists.keys():
			bootlist = bootlists[listname]
			if bootlist['next'] != 'Is Next For Single Use':
				if 1 in bootlist['list'].keys():
					if not re.search(r"(?mi).*(PXE|Network)+", bootlist['list'][1]):
						return False
				else:
					return False
		return True

	@Request_decorator
	def getbootlists(self, sp_system_id=None):
		"""Returns True if boot device set to PXE."""
		if sp_system_id:
			# CQL Support is optional. Too bad :(
			# QUERY=r"""SELECT OBJECTPATH(CIM_ComputerSystem) AS Path FROM CIM_ComputerSystem WHERE ANY CIM_ComputerSystem.IdentifyingDescriptions[*] = '{0}'""".format('CIM:GUID') #, system_uuid)
			for cname in self.__wbempipe.EnumerateInstanceNames('CIM_ComputerSystem'):
				c=self.__wbempipe.GetInstance(cname)
				if 0 not in c['Dedicated']:
					# Not a host (SP maybe)
					continue
				ids = dict(zip(c['IdentifyingDescriptions'],c['OtherIdentifyingInfo']))
				if 'CIM:GUID' in ids.keys() and sp_system_id == ids['CIM:GUID']:
					LOG.debug("Found system %s with path: %s", sp_system_id, c.path)
					s = self.__wbempipe.Associators(c.path, AssocClass='CIM_ServiceAffectsElement', ResultClass='CIM_BootService')
					#QUERY=r"SELECT * FROM CIM_BootService WHERE SystemName = '{0}'".format(c['Name'])
					#LOG.debug("ExecQuery %s", QUERY)
					#s=self.__wbempipe.ExecQuery('CQL',QUERY)
					if not s:
						continue
					LOG.debug("Found service %s", s[0])

					instance = self.__wbempipe.Associators(s[0].path, AssocClass='CIM_ElementCapabilities', ResultClass='CIM_BootServiceCapabilities')
					if isinstance(instance,list) and len(instance) > 0:
						instance=instance[0]
						if 6 in instance['BootConfigCapabilities']:
							LOG.warning("Operation 'Change boot order' is not supported on %s", s[0].path)
							continue
						cap=WBEMC.getHumanValueForList(self.__wbempipe, instance, 'BootConfigCapabilities')
						LOG.debug("CIM_BootServiceCapabilities %s:%s:%s", instance['BootConfigCapabilities'], cap, instance['OtherBootConfigCapabilities'])
					LOG.warning("Operation 'Change boot order' is supported on %s", s[0].path)
					active_bootlists={}
					for bootconfig in self.__wbempipe.References(c.path, ResultClass='CIM_ElementSettingData'):
						bsettings  = bootconfig['SettingData']
						bisdefault = WBEMC.getHumanValue(self.__wbempipe, bootconfig, 'IsDefault')
						bisnext    = WBEMC.getHumanValue(self.__wbempipe, bootconfig, 'IsNext')
						biscurrent = WBEMC.getHumanValue(self.__wbempipe, bootconfig, 'IsCurrent')
						LOG.debug("Found bootconfig %s %s %s %s", bsettings, bisdefault, bisnext, biscurrent)
					for bootlist in self.__wbempipe.Associators(c.path, AssocClass='CIM_ElementSettingData', ResultClass='CIM_BootConfigSetting'):
						LOG.debug("Found bootlist %s", bootlist['ElementName'])
						active_bootlist={}
						a = self.__wbempipe.References(bootlist.path, ResultClass='CIM_ElementSettingData')
						bisdefault = 'unknown'; bisnext = 'unknown'; biscurrent = 'unknown'
						if isinstance(a,list) and len(a) > 0:
							bisdefault = WBEMC.getHumanValue(self.__wbempipe, a[0], 'IsDefault')
							bisnext    = WBEMC.getHumanValue(self.__wbempipe, a[0], 'IsNext')
							biscurrent = WBEMC.getHumanValue(self.__wbempipe, a[0], 'IsCurrent')
							LOG.debug("Bootlist status: %s %s %s", bisdefault, bisnext, biscurrent)
						active_bootlist['default'] = bisdefault
						active_bootlist['next']    = bisnext
						active_bootlist['current'] = biscurrent
						active_bootlist['list']    = {}

						for bootorder in self.__wbempipe.References(bootlist.path, ResultClass='CIM_OrderedComponent'):
							LOG.debug("\t %s %s", bootorder['AssignedSequence'], bootorder['PartComponent'])
							if bootorder['AssignedSequence'] != 0:
								bootdev = self.__wbempipe.GetInstance(bootorder['PartComponent'])
								if bootdev:
									active_bootlist['list'][bootorder['AssignedSequence']] = bootdev['ElementName']
						active_bootlists[bootlist['ElementName']] = active_bootlist
					LOG.debug("\t %s", active_bootlists)
					return active_bootlists


	@Request_decorator
	def getvpd(self):
		"""Returns SP and systems VPD data."""

		system={'macs':{}, 'sn':'', 'model':'', 'power':'' }
		vpd={	'sp':	{'uuid':'', 'mac':'', 'name':'', 'ip':'', 'version':'', 'product':'', 'model':''},
			'sys':	{}}

		for cname in self.__wbempipe.EnumerateInstanceNames('CIM_ComputerSystem'):
			LOG.debug("CIM_ComputerSystem '%s", cname.items())
			c=self.__wbempipe.GetInstance(cname)
			ids  = dict(zip(c['IdentifyingDescriptions'],c['OtherIdentifyingInfo']))
			LOG.debug("ids: '%s", ids)

			uuid = model = sn = makerid = productid = None

			if 'CIM:GUID' in ids.keys():
				uuid = ids['CIM:GUID']
			if 'CIM:Model:SerialNumber' in ids.keys():
				model, sn = ids['CIM:Model:SerialNumber'].split(':')
			if 'Manufacturer ID-Product ID' in ids.keys():
				makerid, productid = ids['Manufacturer ID-Product ID'].split('-')
			if not uuid:
				uuid = c['Name']
				res = re.search(r"(?m)([A-Za-z0-9]{32})", c['Name'])
				if res:
					uuid = res.group(1)

			for dedication in c['Dedicated']:
				if dedication in [ WBEMC.ChassisManager, WBEMC.ManagementController ]:
					# We are in Service Processor association
					LOG.debug("path for SP %s", c.path)
					vpd['sp']['uuid'] = uuid
					vpd['sp']['model'] = model
					vpd['sp']['sn'] = sn
					vpd['sp']['makerid'] = makerid
					vpd['sp']['productid'] = productid
					vpd['sp']['label'] = c['ElementName']
					vpd['sp']['status'] = '/'.join(WBEMC.getHumanValueForList(self.__wbempipe, c, 'OperationalStatus'))

					for instance in self.__wbempipe.Associators(c.path, ResultClass='CIM_NetworkPort'):
						LOG.debug("CIM_NetworkPort for SP %s", instance['BurnedInMAC'])
						vpd['sp']['mac']=instance['BurnedInMAC']

					for instance in self.__wbempipe.Associators(c.path, ResultClass='CIM_IPProtocolEndpoint'):

						ipv4=ipv6=False
						if instance['ProtocolIFType'] == WBEMC.IPv4v6:
							ipv4=ipv6=True
						elif instance['ProtocolIFType'] == WBEMC.IPv6:
							ipv6=True
						elif instance['ProtocolIFType'] == WBEMC.IPv4:
							ipv4=True
						
						if ipv4:
							LOG.debug("CIM_IPProtocolEndpoint for SP IPv4:%s", instance['IPv4Address'])
							vpd['sp']['ipv4']=         instance['IPv4Address']
							vpd['sp']['ipv4_mask']=    instance['SubnetMask']
							vpd['sp']['ipv4_origin']=  WBEMC.getHumanValue(self.__wbempipe, instance, 'AddressOrigin')
							vpd['sp']['ipv4_enabled']= WBEMC.getHumanValue(self.__wbempipe, instance, 'EnabledState')

						if ipv6:
							LOG.debug("CIM_IPProtocolEndpoint for SP IPv6:%s", instance['IPv6Address'])
							vpd['sp']['ipv6']=         instance['IPv6Address']
							vpd['sp']['ipv6_mask']=    instance['PrefixLength']
							vpd['sp']['ipv6_origin']=  WBEMC.getHumanValue(self.__wbempipe, instance, 'AddressOrigin')
							#vpd['sp']['ipv6_type']=    WBEMC.getHumanValue(self.__wbempipe, instance, 'IPv6AddressType')
							vpd['sp']['ipv6_enabled']= WBEMC.getHumanValue(self.__wbempipe, instance, 'EnabledState')

					for instance in self.__wbempipe.Associators(c.path, ResultClass='CIM_DNSProtocolEndpoint'):
						vpd['sp']['name']=instance['Hostname']

					for soft in self.__wbempipe.AssociatorNames(c.path, ResultClass='CIM_SoftwareIdentity'):
						s=self.__wbempipe.GetInstance(soft)
						LOG.debug("CIM_SoftwareIdentity for SP %s version %s", s['InstanceID'], s['VersionString'])
						vpd['sp']['model']=s['InstanceID']
						vpd['sp']['version']=s['VersionString']
						vpd['sp']['version_major']=s['MajorVersion']
						vpd['sp']['version_minor']=s['MinorVersion']
						# String time in CIMDateTime() example '20110209000000.000000+000'
						releasedate=s['ReleaseDate'].datetime
						releasedate=time.mktime(releasedate.timetuple())
						vpd['sp']['version_date']=int(releasedate)
				else:
					# We are in Host association
					if dedication != 0:
						LOG.error("Unsupported CIM_ComputerSystem dedication %s", c.items())
					
					vpd['sys'][uuid] = system
					vpd['sys'][uuid]['sn']    = sn
					vpd['sys'][uuid]['model'] = model
					LOG.debug("path for Host %s", c.path)
					ifaces_ids=set()
					ifaces_count=0
					for iface_name in self.__wbempipe.Associators(c.path, ResultClass='CIM_NetworkPort'):
						LOG.debug("CIM_NetworkPort for Host %s", iface_name['BurnedInMAC'])
						res = re.search(r"(?m)^host-ethernetport-([0-9]+$)", iface_name['DeviceID'])
						if res:
							iface = res.group(1)
							eth_index = str(int(iface) - 1)
						else:
							eth_index = ifaces_count

						while eth_index in ifaces_ids:
							eth_index = eth_index + 1

						ifaces_ids.add(eth_index)
						ifaces_count = ifaces_count + 1
						vpd['sys'][uuid]['macs'][eth_index] = iface_name['BurnedInMAC']

					for instance in self.__wbempipe.Associators(c.path, ResultClass='CIM_Chassis'):
						LOG.debug("CIM_Chassis for Host %s %s %s", instance['Manufacturer'], instance['Model'], instance['SerialNumber'])
						vpd['sys'][uuid]['vendor']       = instance['Manufacturer']
						vpd['sys'][uuid]['partnumber']   = instance['PartNumber']
						vpd['sys'][uuid]['sku']          = instance['SKU']
						vpd['sys'][uuid]['model_name']   = instance['Name']
						vpd['sys'][uuid]['chassis_type'] = WBEMC.getHumanValue(self.__wbempipe, instance, 'ChassisPackageType')
						vpd['sys'][uuid]['package_type'] = WBEMC.getHumanValue(self.__wbempipe, instance, 'PackageType')

					for instance in self.__wbempipe.References(c.path, ResultClass='CIM_AssociatedPowerManagementService'):
						LOG.debug("CIM_AssociatedPowerManagementService for Host %s %s %s", instance['PowerState'])
						vpd['sys'][uuid]['power']        = WBEMC.getHumanValue(self.__wbempipe, instance, 'PowerState')

		LOG.debug("VPD: %s", vpd)
		return vpd

