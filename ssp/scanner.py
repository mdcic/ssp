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

import logging

from   ssp.chassis.common.scanner import COM_SCANNER
import ssp.chassis

__all__ = [ "Scanner" ]
LOG = logging.getLogger("hw.chassis.scanner")


class Scanner:
	"""Represents the scanner able to discover potential service processors on the local network."""

	__name = None
	"""Name of the scanner."""

	__scanners = None
	"""A list of active scan methods."""

	def __init__(self):
		self.__name = c2.misc.get_host_name()
		self.__scanners = {}

		for module_name in c2.hw.chassis.__scanners__:
			module = __import__("c2.hw.chassis." + module_name)
			#for action_name, action_handler in module.ACTIONS.iteritems():
			#	self.__actions["{0}.{1}".format(module_name, action_name)] = action_handler
		for scanner in COM_SCANNER.__subclasses__():
			self.__scanners[scanner.name] = scanner


	def scan(self):
		"""Returns the garbage collector object."""
		all={}
		for s in self.__scanners.keys():
			scanner=self.__scanners[s]()
			r=scanner.scan()
			for rip in r.keys():
				if rip in all.keys():
					all[rip]['proto'].update(r[rip]['proto'])
					all[rip]['scanners'].append(r[rip]['scanners'])
				else:
					all[rip]=r[rip]
		return all
