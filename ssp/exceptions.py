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

class HostIsMissing(core.EC2Error):
	def __init__(self):
		super(HostIsMissing, self).__init__("HostIsMissing", "Host is required, but not specified.")

class ChassisIsAlreadyRegistered(core.EC2Error):
	def __init__(self, message=None):
		super(ChassisIsAlreadyRegistered, self).__init__("ChassisIsAlreadyRegistered", message or "Chassis with specified host is already registered")

class ServiceProcessorTypeIsNeeded(core.EC2Error):
	def __init__(self, message=None):
		super(ServiceProcessorTypeIsNeeded, self).__init__("ServiceProcessorTypeIsNeeded", message or "Service processor type could not be guessed for the host. Please specify.")
