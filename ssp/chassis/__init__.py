#!/usr/bin/env python

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
