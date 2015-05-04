# RICounter
AWS Reservation report generator for EC2, Redshift, and RDS.

Requires boto.  Tested on python 2.7.

For each instance type, in each availability zone, in each selected region, 
RICounter provides the number of running instances, the number of matching
reservations, and the difference between the two.

Negative differences indicate unused reservations, whereas positive differences 
indicate instances not matching a reservation.

```
usage: RICounter.py [-h] [--region REGIONS] [--no-ec2] [--no-rds]
                    [--no-redshift]

optional arguments:
  -h, --help        show this help message and exit
  --region REGIONS  specify region(s) (default is all standard regions)
  --no-ec2          do not check EC2
  --no-rds          do not check RDS
  --no-redshift     do not check Redshift
  --profile PROFILES  specify AWS profile (s) (optional)
 ```

Sample output:

```
EC2 Reservation Report
Instance	Placement	Run	Reserve	Diff
m1.small	us-east-1b	1	0	1
m1.large	us-east-1d	37	32	5
c3.medium	eu-west-1b	14	21	-7
c3.large	us-west-2b	1	1	0
c3.xlarge	us-west-2a	3	3	0

Redshift Reservation Report
NodeType	Region  	Running	Reserve	Diff
dw1.8xlarge	us-east-1	3	6	-3

RDS Reservation Report
Instance	DB	MultiAZ	Region  	Running	Reserve	Diff
db.t2.small	mysql	True	us-east-1	1	1	0
```

Assumes that all ec2 reservations are for the same platform and tenancy.

If an AWS profile (or profiles) are specified, those will be used.  Otherwise,
will use roles or environment variables to authenticate itself to the EC2 API.

Be sure to understand how cross-account billing of reserved instances works
if you're going to specify multiple profiles.  It is useful in the scenario where
a payer account has all of the reservations and the child accounts have the 
actual instances.  It will be extremely misleading in a scenario where reservations
and accounts are scattered between the various accounts