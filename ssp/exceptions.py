from c2 import core

class HostIsMissing(core.EC2Error):
	def __init__(self):
		super(HostIsMissing, self).__init__("HostIsMissing", "Host is required, but not specified.")

class ChassisIsAlreadyRegistered(core.EC2Error):
	def __init__(self, message=None):
		super(ChassisIsAlreadyRegistered, self).__init__("ChassisIsAlreadyRegistered", message or "Chassis with specified host is already registered")

class ServiceProcessorTypeIsNeeded(core.EC2Error):
	def __init__(self, message=None):
		super(ServiceProcessorTypeIsNeeded, self).__init__("ServiceProcessorTypeIsNeeded", message or "Service processor type could not be guessed for the host. Please specify.")
