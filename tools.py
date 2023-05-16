#!/usr/bin/env python3

import os
import argparse
import json

# Import AWS SDK for Python (Boto3)
import boto3
from botocore.exceptions import ClientError


class CloudFormationOrchestrator:
    def __init__(self, region_name, access_key_id, secret_access_key):
        self.cf_client = boto3.client('cloudformation', region_name=region_name, aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
        self.s3_client = boto3.client('s3', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)

    ''' Create VPC stack '''
    def create_vpc_stack(self, args):
        vpc_stack_name = 'my-vpc-stack'
        vpc_params = [{'ParameterKey': 'VpcCidrBlock', 'ParameterValue': args.vpc_cidr_block},
                      {'ParameterKey': 'SubnetCidrBlock', 'ParameterValue': args.subnet_cidr_block}]
        response = self.s3_client.get_object(Bucket=args.template_s3_bucket, Key=args.vpc_template_s3_key)
        vpc_template_body = response['Body'].read().decode('utf-8')
        self.create_stack(vpc_stack_name, vpc_template_body, vpc_params)
        vpc_id = self.get_stack_output(vpc_stack_name, 'VpcId')
        subnet_id = self.get_stack_output(vpc_stack_name, 'SubnetId')

        return {'VpcId': vpc_id, 'SubnetId': subnet_id}

    def create_app_stack(self, args, vpc_id, subnet_id):
        response = self.s3_client.get_object(Bucket=args.template_s3_bucket, Key=args.app_template_s3_key)
        app_template_body = response['Body'].read().decode('utf-8')
        app_stack_name = 'my-web-app-stack'
        app_params = [{'ParameterKey': 'KeyName', 'ParameterValue': args.key_name},
                      {'ParameterKey': 'InstanceType', 'ParameterValue': args.instance_type},
                      {'ParameterKey': 'AmiId', 'ParameterValue': args.ami_id},
                      {'ParameterKey': 'SubnetId', 'ParameterValue': subnet_id},
                      {'ParameterKey': 'VpcId', 'ParameterValue': vpc_id},
                      {'ParameterKey': 'AllowedIp', 'ParameterValue': args.allowed_ip},
                      {'ParameterKey': 'DBUser', 'ParameterValue': args.db_user},
                      {'ParameterKey': 'DBPassword', 'ParameterValue': args.db_password}]
        self.create_stack(app_stack_name, app_template_body, app_params)
        app_url = self.get_stack_output(app_stack_name, 'URL')
        instance_id = self.get_stack_output(app_stack_name, 'InstanceId')
        security_group_id = self.get_stack_output(app_stack_name, 'SecurityGroupId')

        return {
            'AppUrl': app_url,
            'InstanceId': instance_id,
            'SecurityGroupId': security_group_id
        }

    def create_stack(self, stack_name, template_body, parameters):
        try:
            response = self.cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_NAMED_IAM']
            )
            print(f"Creating stack {stack_name}...")
            print(f"Stack creation initiated. Stack ID: {response['StackId']}")

            ''' Creating a waiter object to indicate that we want to wait until the stack is created.'''
            waiter = self.cf_client.get_waiter('stack_create_complete')
            waiter.wait(StackName=stack_name)

            print(f"Stack {stack_name} created successfully.")

        except ClientError as e:
            if 'AlreadyExistsException' in str(e):
                print(f"Stack {stack_name} already exists. Skipping stack creation.")
                return
            print(f"Error creating stack {stack_name}: {e}")
            raise e

    ''' Get Stack Output '''
    def get_stack_output(self, stack_name, output_key):
        try:
            response = self.cf_client.describe_stacks(StackName=stack_name)
            stack = response['Stacks'][0]
            outputs = stack.get('Outputs', [])
            for output in outputs:
                if output['OutputKey'] == output_key:
                    return output['OutputValue']
        except ClientError as e:
            print(f"Error getting output {output_key} from stack {stack_name}: {e}")
            raise e

    ''' Delete Stack'''
    def delete_stack(self, stack_name):
        try:
            self.cf_client.delete_stack(StackName=stack_name)
            print(f"Deleting stack {stack_name}...")
        except ClientError as e:
            if 'Stack with id {} does not exist'.format(stack_name) in str(e):
                print(f"Stack {stack_name} does not exist. Skipping stack deletion.")
                return
            print(f"Error deleting stack {stack_name}: {e}")
            raise e

def main(args):

    orchestrator = CloudFormationOrchestrator(args.region_name, args.aws_access_key_id, args.aws_secret_access_key)
    if args.delete:
        orchestrator.delete_stack('my-web-app-stack')
        orchestrator.delete_stack('my-vpc-stack')
    else:
        vpc_outputs = orchestrator.create_vpc_stack(args=args)
        print(vpc_outputs)
        app_outputs = orchestrator.create_app_stack(args, vpc_outputs['VpcId'], vpc_outputs['SubnetId'])
        print(app_outputs)

    '''Generate a JSON file named according to OutputFileName parameter, and represent the data in JSON format.'''
    if args.output_file_name:
        with open(args.output_file_name, 'w') as f:
            json.dump(app_outputs, f)
        print(f"JSON output file generated: {args.output_file_name}")



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Orchestrate the creation of CloudFormation stacks.')
    parser.add_argument('region_name', type=str, help='AWS region')
    parser.add_argument('aws_access_key_id', type=str, help='AWS access key ID')
    parser.add_argument('aws_secret_access_key', type=str, help='AWS secret access key')
    parser.add_argument('vpc_cidr_block', type=str, help='CIDR block that represents the VPC network', nargs='?', default=None)
    parser.add_argument('subnet_cidr_block', type=str, help='CIDR block that represents the VPC subnet', nargs='?', default=None)
    parser.add_argument('template_s3_bucket', type=str, help='S3 Bucket where template resides', nargs='?', default=None)
    parser.add_argument('vpc_template_s3_key', type=str, help='vpc template key', nargs='?', default=None)
    parser.add_argument('app_template_s3_key', type=str, help='App template key', nargs='?', default=None)
    parser.add_argument('key_name', type=str, help='Name of the SSH Key for the web application instance', nargs='?', default=None)
    parser.add_argument('instance_type', type=str, help='Instance type for the web application instance', nargs='?', default=None)
    parser.add_argument('ami_id', type=str, help='AMI ID to use for the web application instance', nargs='?', default=None)
    parser.add_argument('allowed_ip', type=str, help='IP address to allow HTTP access to in CIDR format', nargs='?', default=None)
    parser.add_argument('db_user', type=str, help='Username for the database', nargs='?', default=None)
    parser.add_argument('db_password', type=str, help='Password for the database', nargs='?', default=None)
    parser.add_argument('output_file_name', type=str, help='Name of the JSON output file', nargs='?', default=None)
    parser.add_argument('--delete', type=bool, help='Delete existing stacks', nargs='?', default=None)
    args = parser.parse_args()

    print(f"Received arguments: {args}")

    main(args)