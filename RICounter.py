#!/usr/bin/env python2.7

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
parser.add_argument('--only-variance', action="store_true", dest="only_variance", default=False, help="only output lines with a variance")
parser.add_argument('--profile', action="append", dest="profiles", default=None, help="specify AWS profile (s) (optional)")

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
        variance = running[key] - reserved[key]
        if args.only_variance is False or abs(variance) > 0:
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

profiles = [None] if args.profiles is None else args.profiles

if args.ec2:
    print "EC2 Reservation Report"
    print "Instance\tPlacement\tRun\tReserve\tDiff"
    for region in regions['ec2']:
        running_instances = defaultdict(int)
        reserved_instances = defaultdict(int)

        for profile in profiles:
            ec2 = region.connect(profile_name=profile)

            running = ec2.get_all_reservations(filters={'instance-state-name': 'running'})
            for r in running:
                for i in r.instances:
                    running_instances[i.instance_type + "\t" + i.placement] += 1

            for ri in ec2.get_all_reserved_instances(filters={'state': ['active', 'payment-pending']}):
                reserved_instances[ri.instance_type + "\t" + ri.availability_zone] += ri.instance_count

        print_results(running_instances, reserved_instances)

# Redshift
if args.redshift:
    print "Redshift Reservation Report"
    print "NodeType\tRegion  \tRunning\tReserve\tDiff"
    for region in regions['redshift']:
        running_nodes = defaultdict(int)
        reserved_nodes = defaultdict(int)

        for profile in profiles:
            conn = boto.redshift.connect_to_region(region.name, profile_name=profile)

            cluster_response = conn.describe_clusters()
            for cluster in cluster_response['DescribeClustersResponse']['DescribeClustersResult']['Clusters']:
                running_nodes[cluster['NodeType'] + "\t" + region.name] += cluster['NumberOfNodes']

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
        running_rds = defaultdict(int)
        reserved_rds = defaultdict(int)

        for profile in profiles:
            conn = boto.rds2.connect_to_region(region.name, profile_name=profile)

            rdb_response = conn.describe_db_instances()
            for db in rdb_response['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances']:
                running_rds[db['DBInstanceClass'] + "\t" + db['Engine'] + "\t" + str(db['MultiAZ']) + "\t" + region.name] += 1

            reservation_response = conn.describe_reserved_db_instances()
            active_reservations = [x for x in reservation_response['DescribeReservedDBInstancesResponse']['DescribeReservedDBInstancesResult']['ReservedDBInstances'] if x['State'] in ('active', 'payment-pending')]
            for r in active_reservations:
                reserved_rds[r['DBInstanceClass'] + "\t" + r['ProductDescription'] + "\t" + str(db['MultiAZ']) + "\t" + region.name] += r['DBInstanceCount']

        print_results(running_rds, reserved_rds)
