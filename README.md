# RICounter
AWS Reserved Instance Counter

Requires boto.  Tested on python 2.7.

Will use roles or environment variables to authenticate itself to the EC2 API.

For each instance type, in each availability zone, in each selected region, 
RICounter provides the number of running instances, the number of matching
reservations, and the difference between the two.

Negative differences indicate unused reservations.
Positive differences indicate instances not matching a reservation.

usage: RICounter.py [-h] [--region REGIONS]

optional arguments:
  -h, --help        show this help message and exit
  --region REGIONS  specify a region (default is all standard regions)
Sample output:

`
Instance    AZ      Run Reserve Diff
c3.2xlarge  us-east-1b  3   3   0
c3.2xlarge  us-east-1d  2   2   0
c4.large    us-east-1b  2   2   0
c4.large    us-east-1d  2   2   0
c4.large    us-east-1e  2   2   0
m1.large    us-east-1b  3   4   -1
c3.xlarge   eu-west-1b  3   3   0
c3.xlarge   eu-west-1c  3   3   0
m3.2xlarge  eu-west-1b  14  13  1
m3.2xlarge  eu-west-1c  13  13  0
c3.large    us-west-2a  1   1   0
c3.large    us-west-2b  1   1   0
c3.large    us-west-2c  1   1   0
c3.xlarge   us-west-2a  3   3   0
c3.xlarge   us-west-2b  3   3   0
c3.xlarge   us-west-2c  3   3   0
`