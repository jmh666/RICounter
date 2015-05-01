#!/usr/bin/env python

"""
RICounter - Creates an RI usage report.

negative balances indicate excess reserved instances
positive balances indicate instances that are not falling under RIs
"""
import argparse

from collections import defaultdict

import boto.ec2

parser = argparse.ArgumentParser()
parser.add_argument('--region', action="append", dest="regions", 
	help="specify a region (default is all standard regions)")
args = parser.parse_args()

instance_filters = {
	'instance-state-name': 'running'
}
reservation_filters = {
	'state': 'active'
}

print "Instance\tAZ\t\tRun\tReserve\tDiff"

if args.regions is None:
	DISABLED_REGIONS = ['cn-north-1', 'us-gov-west-1']
	regions = [ r for r in boto.ec2.regions() if r.name not in DISABLED_REGIONS ]
else:
	regions = [ r for r in boto.ec2.regions() if r.name in args.regions ]

for region in regions:
	ec2 = region.connect()

	running_instances = defaultdict(int)
	running = ec2.get_all_reservations(filters=instance_filters)
	for r in running:
		for i in r.instances:
			running_instances[i.instance_type + "\t" + i.placement] += 1

	reserved_instances = defaultdict(int)
	for ri in ec2.get_all_reserved_instances(filters=reservation_filters):
		reserved_instances[ri.instance_type + "\t" + ri.availability_zone] += ri.instance_count

	keys = set(reserved_instances.keys() + running_instances.keys())
	if len(keys) == 0:
		continue

	for key in sorted(keys):
		print "%s\t%d\t%d\t%d" % (key, running_instances[key], reserved_instances[key], 
			running_instances[key] - reserved_instances[key])
