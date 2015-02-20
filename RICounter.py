#!/usr/bin/env python

"""
RICounter - outputs RI balance for the current AWS region

negative balances indicate excess reserved instances
positive balances indicate instances that are not falling under RIs
"""

from collections import Counter;
from os import getenv;
import boto.ec2;
import boto.rds;

DISABLED_REGIONS = ['cn-north-1', 'us-gov-west-1'];

regions = boto.ec2.regions();

for region in regions:
	if region.name in DISABLED_REGIONS:
		continue;

	try:
		ec2 = region.connect();

		reservations = ec2.get_all_reservations();
	except Exception as e:
		logging.warning("Could not get instance reservations for region: " + region.name + " (" + e.message + ")");
		continue;


	instances = [i.placement + ' - ' + i.instance_type for r in reservations for i in r.instances if i.state == 'running'];

	instance_counter = Counter(instances);

	for ri in ec2.get_all_reserved_instances():
		if ri.state == 'active':
			instance_counter.subtract({ri.availability_zone + ' - ' + ri.instance_type: ri.instance_count});

	for key in sorted(instance_counter.keys()):
		print "%s\t%d" % (key, instance_counter[key]);
