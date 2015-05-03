#!/usr/bin/env python

"""
RICounter - Creates reservation reports for EC2, Redshift, and RDS.
"""
import argparse
import re

from collections import Counter
from collections import defaultdict

import boto.ec2
import boto.rds2
import boto.redshift

parser = argparse.ArgumentParser()
parser.add_argument('--region', action="append", dest="regions", help="specify region(s) (default is all standard regions)")
parser.add_argument('--no-ec2', action="store_false", dest="ec2", default=True, help="do not check EC2")
parser.add_argument('--no-rds', action="store_false", dest="rds", default=True, help="do not check RDS")
parser.add_argument('--no-redshift', action="store_false", dest="redshift", default=True, help="do not check Redshift")
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

def print_results(running, reserved):
    keys = set(running.keys() + reserved.keys())
    for key in sort_instances(keys):
        print "%s\t%d\t%d\t%d" % (key, running[key], reserved[key], running[key] - reserved[key])


regions = {}
if args.regions is None:
    regions['ec2'] = [r for r in boto.ec2.regions() if r.name not in DISABLED_REGIONS]
    regions['redshift'] = [r for r in boto.redshift.regions() if r.name not in DISABLED_REGIONS]
    regions['rds'] = [r for r in boto.rds2.regions() if r.name not in DISABLED_REGIONS]
else:
    regions['ec2'] = [r for r in boto.ec2.regions() if r.name in args.regions]
    regions['redshift'] = [r for r in boto.redshift.regions() if r.name in args.regions]
    regions['rds'] = [r for r in boto.rds2.regions() if r.name in args.regions]

if args.ec2:
    print "EC2 Reservation Report"
    print "Instance\tPlacement\tRun\tReserve\tDiff"
    for region in regions['ec2']:
        ec2 = region.connect()

        running = ec2.get_all_reservations(filters={'instance-state-name': 'running'})
        running_instances = Counter([i.instance_type + "\t" + i.placement for r in running for i in r.instances])

        reserved_instances = defaultdict(int)
        for ri in ec2.get_all_reserved_instances(filters={'state': ['active', 'payment-pending']}):
            reserved_instances[ri.instance_type + "\t" + ri.availability_zone] += ri.instance_count

        print_results(running_instances, reserved_instances)

# Redshift
if args.redshift:
    print "Redshift Reservation Report"
    print "NodeType\tRegion  \tRunning\tReserve\tDiff"
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

        print_results(running_nodes, reserved_nodes)

# RDS
if args.rds:
    print "RDS Reservation Report"
    print "Instance\tDB\tMultiAZ\tRegion  \tRunning\tReserve\tDiff"
    for region in regions['rds']:
        conn = boto.rds2.connect_to_region(region.name)

        rdb_response = conn.describe_db_instances()
        running_rds = Counter([db['DBInstanceClass'] + "\t" + db['Engine'] + "\t" + str(db['MultiAZ']) + "\t" + region.name for db in rdb_response['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances']])

        reserved_rds = defaultdict(int)
        reservation_response = conn.describe_reserved_db_instances()
        active_reservations = [x for x in reservation_response['DescribeReservedDBInstancesResponse']['DescribeReservedDBInstancesResult']['ReservedDBInstances'] if x['State'] in ('active', 'payment-pending')]
        for r in active_reservations:
            reserved_rds[r['DBInstanceClass'] + "\t" + r['ProductDescription'] + "\t" + str(db['MultiAZ']) + "\t" + region.name] += r['DBInstanceCount']

        print_results(running_rds, reserved_rds)

