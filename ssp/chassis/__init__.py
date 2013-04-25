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

"""Contains controls for various server hardware chassises."""


__open__ = [
	"ipmi.v2",
	"wbem.generic"
]

__proprietary__ = [
	"dell.idrac6",
	"ibm.imm"
]

__all__ = __proprietary__ + __open__

__scanners__ = [
	"ipmi.scanner",
	"wbem.scanner",
	"ibm.scanner"
]

_HWCONTROLS = set([])

"""Available Service Processor control methods."""


def register_handlers(other):
	"""Register additional handlers"""

	_HWCONTROLS.update(other)


def get_handler(action):
	"""Get registered handler by action name"""

	return _HWCONTROLS.get(action)


def request_handler(action, template):
	"""Decorator for registering hwcontrol handlers."""

	def wrap(func):
		def wrapper(user_id, request):
			return func(user_id, request)

		_HWCONTROLS[action] = wrapper
		return wrapper

	return wrap
