#!/usr/bin/env python3

import os
import json
import ast

# Import AWS SDK for Python (Boto3)
import boto3
from botocore.exceptions import ClientError

class CloudFormationOrchestrator:
    def __init__(self, region_name, access_key_id, secret_access_key):
        self.cf_client = boto3.client('cloudformation', region_name=region_name, aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
        self.s3_client = boto3.client('s3', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)

    ''' Create VPC stack '''
    def create_vpc_stack(self, vpc_cidr_block, subnet_cidr_block, template_s3_bucket, vpc_template_s3_key):
        vpc_stack_name = 'my-vpc-stack'
        vpc_params = [{'ParameterKey': 'VpcCidrBlock', 'ParameterValue': vpc_cidr_block},
                      {'ParameterKey': 'SubnetCidrBlock', 'ParameterValue': subnet_cidr_block}]
        response = self.s3_client.get_object(Bucket=template_s3_bucket, Key=vpc_template_s3_key)
        vpc_template_body = response['Body'].read().decode('utf-8')
        self.create_stack(vpc_stack_name, vpc_template_body, vpc_params)
        vpc_id = self.get_stack_output(vpc_stack_name, 'VpcId')
        subnet_id = self.get_stack_output(vpc_stack_name, 'SubnetId')

        return {'VpcId': vpc_id, 'SubnetId': subnet_id}

    def create_app_stack(self, vpc_id, subnet_id, template_s3_bucket, app_template_s3_key, key_name, instance_type, ami_id, allowed_ip, db_user, db_password):
        response = self.s3_client.get_object(Bucket=template_s3_bucket, Key=app_template_s3_key)
        app_template_body = response['Body'].read().decode('utf-8')
        app_stack_name = 'my-web-app-stack'
        app_params = [{'ParameterKey': 'KeyName', 'ParameterValue': key_name},
                      {'ParameterKey': 'InstanceType', 'ParameterValue': instance_type},
                      {'ParameterKey': 'AmiId', 'ParameterValue': ami_id},
                      {'ParameterKey': 'SubnetId', 'ParameterValue': subnet_id},
                      {'ParameterKey': 'VpcId', 'ParameterValue': vpc_id},
                      {'ParameterKey': 'AllowedIp', 'ParameterValue': allowed_ip},
                      {'ParameterKey': 'DBUser', 'ParameterValue': db_user},
                      {'ParameterKey': 'DBPassword', 'ParameterValue': db_password}]
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


def main():
    region_name = os.environ.get('AWS_REGION')
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    vpc_cidr_block = os.environ.get('VPC_CIDR_BLOCK')
    subnet_cidr_block = os.environ.get('SUBNET_CIDR_BLOCK')
    template_s3_bucket = os.environ.get('TEMPLATE_S3_BUCKET')
    vpc_template_s3_key = os.environ.get('VPC_TEMPLATE_S3_KEY')
    app_template_s3_key = os.environ.get('APP_TEMPLATE_S3_KEY')
    key_name = os.environ.get('KEY_NAME')
    instance_type = os.environ.get('INSTANCE_TYPE')
    ami_id = os.environ.get('AMI_ID')
    allowed_ip = os.environ.get('ALLOWED_IP')
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    output_file_name = os.environ.get('OUTPUT_FILE_NAME')
    delete = os.environ.get('DELETE', 'False')

    delete_bool = ast.literal_eval(delete)

    orchestrator = CloudFormationOrchestrator(region_name, aws_access_key_id, aws_secret_access_key)

    print("Starting execution")
    if delete_bool:
        orchestrator.delete_stack('my-web-app-stack')
        orchestrator.delete_stack('my-vpc-stack')
    else:
        vpc_outputs = orchestrator.create_vpc_stack(vpc_cidr_block, subnet_cidr_block, template_s3_bucket, vpc_template_s3_key)
        app_outputs = orchestrator.create_app_stack(vpc_outputs['VpcId'], vpc_outputs['SubnetId'], template_s3_bucket, app_template_s3_key, key_name, instance_type, ami_id, allowed_ip, db_user, db_password)

        '''Generate a JSON file named according to OutputFileName parameter, and represent the data in JSON format.'''
        if output_file_name:
            with open(output_file_name, 'w') as f:
                json.dump(app_outputs, f, indent=4)
            print(f"JSON output file generated: {output_file_name}")


if __name__ == '__main__':
    main()