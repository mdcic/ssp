#!/usr/bin/env python

"""Gives a facility to control several types of Service Processors"""

import logging
import subprocess
import time
import re

import ssp.identify
from ssp.chassis.dell.idrac6 import DELLiDRAC6


__all__ = [ "ServiceProcessor" ]
LOG = logging.getLogger("ssp.chassis.service_processor")

SSH_PUBKEY  = "/etc/c2/hw-ssh-pubkey.pem"
SSH_PRIVKEY = "/etc/c2/hw-ssh-privkey.pem"
SSH_SSLCRT  = "/etc/c2/hw-ssl.crt"
KNOWN_SPTYPES = ('DELL-iDRAC6','IBM-RSA','IBM-BLADECENTER','HP-iLO')

def Request_decorator(func):
	"""Logs all requests."""

	def decorator(self, *args, **kwargs):
		if kwargs:
			LOG.info("%s(%s)%s called.", func.func_name, args, kwargs)
		else:
			LOG.info("%s(%s) called.", func.func_name, args)

		return func(self, *args, **kwargs)

	return decorator


class ServiceProcessor:
	"""Represents an abstract Service Processor."""

	__host = None
	"""host name or IP. Must be specified."""

	__type = None
	"""type of the SP. Could be guessed"""

	__user = None
	"""User name for logging in. Will use Factory default if exists."""

	__password = None
	"""Password for logging in. Will use Factory default if exists."""

	__secret = None
	"""Key to use for SSH connection. If specified will be used insted of password for ssh."""
	"""Or cert to use for SSL connection. If specified will be used instead of password for ssl."""

	__uuid = None
	"""Internal chassis Id. If specified will be compared to actual uuid for all commands."""

	__vpd = {}
	"""Most current chassis info."""

	def __init__(self, host=None, type=None, user=None, password=None, secret=None, uuid=None):
		self.__host = host
		self.__type = type
		self.__user = user
		self.__password = password
		self.__secret = secret
		self.__uuid = uuid

	def __spcontrol(self, sptype, host, user, password):
		"""Return SP object for sptype."""
		
		if sptype == "DELL-iDRAC6":
			return DELLiDRAC6(host, user, password)

	def __validate_sptype(self, sptype, host, user, password):
		"""Check if given sptype is indeed correct."""
		
		sp=self.__spcontrol(sptype, host, user, password)
		if sp.connect():
			sp.disconnect()
			return True
		return False

	@Request_decorator
	def __trydefaultcred(self, sptype):
		"""Try to authenticate on SP with given or default credentials."""
		
		user=self.__user
		password=self.__password
		if sptype not in KNOWN_SPTYPES:
			LOG.error("Unknown service processor type")
			return False
		if not user:
			user = ssp.chassis.identify.defaults[sptype]['user']
		if not password:
			password = ssp.chassis.identify.defaults[sptype]['pass']
		if user and password and self.__host:
			if self.__validate_sptype(sptype, self.__host, user, password):
				self.__type = sptype
				self.__user = user
				self.__password = password
				return True

	@Request_decorator
	def guess_type_and_creds(self):
		"""Identify the type of SP and credentials."""

		if not self.__host:
			raise Error("Host is required, but not specified.")
		trylist = ssp.chassis.identify.suggest_sptype(self.__host)
		if trylist:
			for sptype in [trylist]:
				if self.__trydefaultcred(sptype):
					return True
		return False

	@Request_decorator
	def updatevpd(self):
		"""Retrieve HW data from SP."""
		
		c = self.__spcontrol(self.__type, self.__host, self.__user, self.__password)
		c.connect()
		self.__vpd=c.getvpd()
		c.disconnect()

	@Request_decorator
	def getHost(self):
		"""Return host of current SP."""
		return self.__host

	@Request_decorator
	def getType(self):
		"""Return type of current SP."""
		return self.__type

	@Request_decorator
	def getUser(self):
		"""Return user of current SP."""
		return self.__user

	@Request_decorator
	def getPassword(self):
		"""Return password of current SP."""
		return self.__password

	@Request_decorator
	def getSecret(self):
		"""Return secret (SSH key or SSL cert) of current SP."""
		return self.__secret

	@Request_decorator
	def getGUID(self):
		"""Return GUID of current SP."""
		return self.__uuid

	@Request_decorator
	def getVPD(self):
		"""Return HW VPD of current SP."""
		return self.__vpd

