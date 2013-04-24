#!/usr/bin/env python

"""Contains constants and maps for WBEM Service Processors."""

ChassisManager = 29
ManagementController = 28
IPv4 = 4096
IPv6 = 4097
IPv4v6 = 4098


def getEnabledState_human(code=None):
	"""Given status code return interface status string"""

	IFACE_STATUS={0:'Unknown', 1:'Other', 2:'Enabled', 3:'Disabled', 4:'Shutting Down',
                      5:'Not Applicable', 6:'Enabled but Offline', 7:'In Test', 8:'Deferred',
                      9:'Quiesce', 10:'Starting'}

	if code in IFACE_STATUS.keys():
		return IFACE_STATUS[code]
	if code >= 11 and  code <= 32767:
		return 'DMTF Reserved'
	if code >= 32768 and  code <= 65535:
		return 'Vendor Reserved'
	return 'out of range'

def getHumanValue(connection=None, instance=None, property=None):
	"""Resolve numeric value to human readable string if available"""
	
	vali = instance[property]
	if isinstance(vali,list):
		vali=vali[0]
	val  = str(vali)
	wbclass = connection.GetClass(instance.classname, IncludeQualifiers=True)
	q = wbclass.properties[property].qualifiers
	if 'ValueMap' in q.keys() and 'Values' in q.keys():
		ids  = dict(zip(q['ValueMap'].value, q['Values'].value))
		print ids, val, vali
		if val in ids.keys():
			return ids[val]
		else:
			# It might by a range like '31..23000'
			for i in ids.keys():
				try:
					min, max = i.split('..')
					min=int(min)
					max=int(max)
					if vali >= min and vali <= max:
						return ids[i]
				except ValueError:
					pass
	else:
		return val
	return None

def getHumanValueForList(connection=None, instance=None, property=None):
	"""Resolve numeric value to human readable string if available"""

	result=[]
	for vali in instance[property]:
		val  = str(vali)
		wbclass = connection.GetClass(instance.classname, IncludeQualifiers=True)
		q = wbclass.properties[property].qualifiers
		if 'ValueMap' in q.keys() and 'Values' in q.keys():
			ids  = dict(zip(q['ValueMap'].value, q['Values'].value))
			print ids, val, vali
			if val in ids.keys():
				result.append(ids[val])
				continue
			else:
				# It might by a range like '31..23000'
				for i in ids.keys():
					try:
						min, max = i.split('..')
						min=int(min)
						max=int(max)
						if vali >= min and vali <= max:
							result.append(ids[i])
							break
					except ValueError:
						pass
	if result == []:
		return None
	else:
		return result

