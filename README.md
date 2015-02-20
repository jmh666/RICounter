# RICounter
AWS Reserved Instance Counter

Requires boto.  Tested on python 2.7.

Will use roles or environment variables to authenticate itself to the EC2 API.

Negative numbers indicate excess/unused RIs provisioned for that instance type in that AZ

Positive numbers indicate un-reserved instances of that type in that AZ

Usage: ./RICounter.py

Sample output:

    us-east-1b - c3.xlarge  0
    us-east-1b - m1.small   1
    us-east-1b - m3.large   1
    us-east-1b - m3.medium  2
    us-east-1c - c1.xlarge  0
    us-east-1c - c3.2xlarge 0
    us-east-1c - c3.large   2
    us-east-1c - m1.large   1
    us-east-1c - m1.small   3
    us-east-1c - m1.xlarge  1
    us-east-1c - m3.large   2
    us-east-1c - m3.medium  2
    us-east-1c - m3.xlarge  0
    us-east-1c - t1.micro   2
    us-east-1d - m1.xlarge  1
    us-east-1e - t1.micro   1
    us-west-1c - t1.micro   1
