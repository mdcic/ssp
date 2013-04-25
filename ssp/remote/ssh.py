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

"""Gives a facility to control SSH commands"""

import logging
import paramiko
import re

__all__ = [ "SSHchannel" ]
LOG = logging.getLogger("ssp.hw.remote.ssh")

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


class SSHchannel:
	"""Represents an SSH command shell."""

	__host = None
	"""host name or IP."""

	__port = None
	"""port number."""

	__user = None
	"""User name."""

	__password = None
	"""Password."""

	__sshprivkey = None
	"""Key to use for SSH connection."""

	__sshclient = None
	"""SSH client object."""

	def __init__(self, host, port=22, user=None, password=None):
		self.__host = host
		self.__port = port
		self.__user = user
		self.__password = password
		self.__sshclient = paramiko.SSHClient()
		self.__sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

	@Request_decorator
	def connect(self):
		"""Attempt authenticated ssh connection to service processor."""
		try:
			self.__sshclient.load_system_host_keys()
			self.__sshclient.connect(self.__host, port=self.__port, username=self.__user, password=self.__password, allow_agent=False)
		except Exception, e:
			LOG.error("Failed to connect to '%s'. %s", self.__host, e)
			raise
		return True


	@Request_decorator
	def disconnect(self):
		"""Close authenticated ssh connection to service processor."""
		try:
			self.__sshclient.close()
		except Exception, e:
			LOG.error("Failed to disconnect to '%s'. %s", host, e)
			raise
		return True


	@Request_decorator
	def guessType(self):
		"""Returns string representing possible type of service processor."""

		stdout = self.command("racadm help")
		sptype = stdout.splitlines()[-2].strip()

		if sptype not in ("idrac", "rsa", "ilo"):
			LOG.error("SP %s is off unknown type. %s",
				self.__host, sptype)
			state = "unknown"

		return state


	def command(self, command):
		"""Executes a command on service processor."""

		LOG.info("Executing command '%s' for %s...", command, self.__host)
		output = None
		try:
			stdin, stdout, stderr = self.__sshclient.exec_command(command)
			if stdout:
				output = stdout.read()
				LOG.debug("Output for command '%s' for %s:\n%s", command, self.__host, output)
			if stderr:
				LOG.debug("Error output for command '%s' for %s:\n%s", command, self.__host, stderr.read())

			return output
		except Exception, e:
			LOG.error("Failed to execute command '%s' for %s. %s", command, self.__host, e)
			raise

	@Request_decorator
	def simplecommand(self, command, regexp):
		"""run command on SP and validate reply through regexp."""

		stdout = self.command(command)
		if re.search(regexp, stdout):
			return True
		else:
			return False


	@Request_decorator
	def smartcommand(self, command, regexp, finnalize_info=None):
		"""run command on SP and validate reply through regexp and valid replys list."""

		stdout = self.command(command)
		reply = re.search(regexp, stdout)

		if reply != None:
		    reply=reply.group(0).lower().strip()
		else:
			return "UNKNOWN"

		if finnalize_info != None:
			for listid in finnalize_info.keys():
				if reply in finnalize_info[listid]:
					return listid
			LOG.error("SP %s replied something new '%s'. Treating it as 'unknown'.",
				self.__host, reply)
			return "UNKNOWN"
		else:
			return reply
