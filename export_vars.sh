#!/bin/bash

export AWS_REGION=us-west-2
export VPC_CIDR_BLOCK=10.0.0.0/21
export SUBNET_CIDR_BLOCK=10.0.0.0/24
export TEMPLATE_S3_BUCKET=intuit-onsite2023
export VPC_TEMPLATE_S3_KEY=CF1-VPC.json
export APP_TEMPLATE_S3_KEY=CF2-WebApplication.json
export KEY_NAME=IntuitOnsite
export INSTANCE_TYPE=t2.micro
export AMI_ID=ami-e689729e
export ALLOWED_IP=0.0.0.0/0
export DB_USER=admin
export DB_PASSWORD=q1w2e3r4
export OUTPUT_FILE_NAME=deployment_1
