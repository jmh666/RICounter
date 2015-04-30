#!/usr/bin/env python

"""
RICounter - outputs RI balance for the current AWS region

negative balances indicate excess reserved instances
positive balances indicate instances that are not falling under RIs
"""

from collections import Counter

import boto.ec2

DISABLED_REGIONS = ['cn-north-1', 'us-gov-west-1']

for region in [ r for r in boto.ec2.regions() if r.name not in DISABLED_REGIONS ]:
	ec2 = region.connect()

	reservations = ec2.get_all_reservations(filters={'instance-state-name':'running'})
	instances = [i.instance_type + ' - ' + i.placement for r in reservations for i in r.instances]

	instance_counter = Counter(instances)

	for ri in ec2.get_all_reserved_instances(filters={'state' : 'active'}):
		instance_counter.subtract({ri.instance_type + ' - ' + ri.availability_zone : ri.instance_count})

	for key in sorted(instance_counter.keys()):
		print "%s\t%d" % (key, instance_counter[key])