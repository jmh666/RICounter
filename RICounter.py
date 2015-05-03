#!/usr/bin/env python

"""
RICounter - Creates an RI usage report.

negative balances indicate excess reserved instances
positive balances indicate instances that are not falling under RIs
"""
import argparse
import re

from collections import defaultdict

import boto.ec2
import boto.rds2
import boto.redshift

parser = argparse.ArgumentParser()
parser.add_argument('--region', action="append", dest="regions", help="specify a region (default is all standard regions)")
args = parser.parse_args()

DISABLED_REGIONS = ['cn-north-1', 'us-gov-west-1']


def sort_instances(instances):
    size_order = {'micro': 0, 'small': 1, 'medium': 2, 'large': 3, 'xlarge': 4, '2xlarge': 5, '4xlarge': 6, '8xlarge': 7}
    def instance_key(instance):
        if instance[0:3] == 'db.':
            family, size = re.split('\W', instance)[1:3]
        else:
            family, size = re.split('\W', instance)[0:2]
        return family + str(size_order[size])
    return sorted(instances, key=instance_key)

regions = {}
if args.regions is None:
    regions['ec2'] = [r for r in boto.ec2.regions() if r.name not in DISABLED_REGIONS]
    regions['redshift'] = [r for r in boto.redshift.regions() if r.name not in DISABLED_REGIONS]
    regions['rds'] = [r for r in boto.rds2.regions() if r.name not in DISABLED_REGIONS]
else:
    regions['ec2'] = [r for r in boto.ec2.regions() if r.name in args.regions]
    regions['redshift'] = [r for r in boto.redshift.regions() if r.name in args.regions]
    regions['rds'] = [r for r in boto.rds2.regions() if r.name in args.regions]

print "Instance\tAZ\t\tRun\tReserve\tDiff"
for region in regions['ec2']:
    ec2 = region.connect()

    running_instances = defaultdict(int)
    running = ec2.get_all_reservations(filters={'instance-state-name': 'running'})
    for r in running:
        for i in r.instances:
            running_instances[i.instance_type + "\t" + i.placement] += 1

    reserved_instances = defaultdict(int)
    for ri in ec2.get_all_reserved_instances(filters={'state': 'active', 'state': 'payment-pending'}):
        reserved_instances[ri.instance_type + "\t" + ri.availability_zone] += ri.instance_count

    keys = set(reserved_instances.keys() + running_instances.keys())
    for key in sort_instances(keys):
        print "%s\t%d\t%d\t%d" % (key, running_instances[key], reserved_instances[key], running_instances[key] - reserved_instances[key])

# RedShift
for region in regions['redshift']:
    conn = boto.redshift.connect_to_region(region.name)

    running_nodes = defaultdict(int)
    cluster_response = conn.describe_clusters()
    for cluster in cluster_response['DescribeClustersResponse']['DescribeClustersResult']['Clusters']:
        running_nodes[cluster['NodeType'] + "\t" + region.name] += cluster['NumberOfNodes']

    reserved_nodes = defaultdict(int)
    reservation_response = conn.describe_reserved_nodes()
    active_reservations = [x for x in reservation_response['DescribeReservedNodesResponse']['DescribeReservedNodesResult']['ReservedNodes'] if x['State'] in ('active', 'payment-pending')]
    for reservation in active_reservations:
        reserved_nodes[reservation['NodeType'] + "\t" + region.name] += reservation['NodeCount']

    keys = set(reserved_nodes.keys() + running_nodes.keys())
    for key in sort_instances(keys):
        print "Redshift-%s\t%d\t%d\t%d" % (key, running_nodes[key], reserved_nodes[key], running_nodes[key] - reserved_nodes[key])

# RDS
for region in regions['rds']:
    conn = boto.rds2.connect_to_region(region.name)

    running_rds = defaultdict(int)
    rdb_response = conn.describe_db_instances()
    for db in rdb_response['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances']:
        az = "MultiAZ" if db['MultiAZ'] else "SingleAZ"
        running_rds[db['DBInstanceClass'] + "\t" + db['Engine'] + "\t" + az + "\t" + region.name] += 1

    reserved_rds = defaultdict(int)
    reservation_response = conn.describe_reserved_db_instances()
    active_reservations = [x for x in reservation_response['DescribeReservedDBInstancesResponse']['DescribeReservedDBInstancesResult']['ReservedDBInstances'] if x['State'] in ('active', 'payment-pending')]
    for r in active_reservations:
        az = "MultiAZ" if r['MultiAZ'] else "SingleAZ"
        reserved_rds[r['DBInstanceClass'] + "\t" + r['ProductDescription'] + "\t" +  az + "\t" + region.name] += r['DBInstanceCount']

    keys = set(reserved_rds.keys() + running_rds.keys())
    for key in sort_instances(keys):
        print "RDS-%s\t%d\t%d\t%d" % (key, running_rds[key], reserved_rds[key], running_rds[key] - reserved_rds[key])

