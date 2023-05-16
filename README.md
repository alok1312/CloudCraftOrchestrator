# CloudCraftOrchestrator
# Craft Demo - Goal

The goal of this craft demo is to take the two provided CloudFormation
templates, and orchestrate their creation using a Python/Boto wrapper run inside a docker container deployed on a kubernetes cluster.

Your primary goal is to create a command line tool that creates the stacks by taking in a minimal
set of parameters, package the command line tool in a docker image and deploy on a locally running kubernetes cluster as a "Job".

You should make use of the stacks outputs to limit the amount of parameters your script requires.

## Instructions

Try to concentrate on your code design and quality.
If possible try using advanced development practices, such as OOP, decorators, python lambdas, nested lists, etc.

Your code should be able to handle exceptions from AWS API and your own functions, and retry if something fails.

Design-wise, try to think about simplifying things for who ever will be running this tool, the user experience is extremely important.

Note:
Supplied template deployment had been successfully tested with ami-e689729e
('amzn-ami-hvm-2017.09.0.20170930-x86_64-gp2' in us-west-2 region) on a t2.micro machine.

Use Secure best practices while building the docker image.

## Bonus Features
Monitoring - Add a simple monitoring solution / agent to the application server.
You can use any free tier SaaS tool out there (e.g. DataDog), and create a few simple dashboards that will monitor relevant metrics according to the components on the EC2 instance - You may modify the CloudFormation templates for that purpose.

## Craft Demo Expectations 
There are various ways to complete this craft demo. Below are expected artifacts for the demo: 
1. A docker image uploaded to hub.docker.com which takes in necessary aws credentials and script parameters as environment variable to run the script on other AWS accounts.
2. A kubernetes yaml spec file for deploying the above docker image as a Job(Kind).
3. Demo output of above kubernetes job run in a local kubernetes cluster which creates VPC and creates a simple web application in a free tier AWS Account.


# Setup and available resources and files

## AWS Compute Resources:
Please note this Craft demo can be provisioned using resources with zero cost using an AWS free tier account.

## Docker and Kubernetes Setup : 
1. You can use Docker for Desktop to enable installation of a local Kubernetes cluster
Example: https://andrewlock.net/running-kubernetes-and-the-dashboard-with-docker-desktop/

2. Alternatively you can use other local Kubernetes clusters, such as Kind or k3s
Example: https://kind.sigs.k8s.io/docs/user/quick-start/ , https://k3s.io/

## CloudFormation Template Files

### CF1-VPC.json

This CloudFormation template creates a simple VPC, and requires the following
parameters:

- VpcCidrBlock - A CIDR block that represents the network, i.e. 10.0.0.0/21
- SubnetCidrBlock - A CIDR block that represents a single subnet within
the network, i.e. 10.0.0.0/24 or 10.0.1.0/24, etc.

Outputs are:

- VpcId - The ID of the resulting VPC
- SubnetId - The ID of the resulting Subnet

### CF2-WebApplication.json

This CloudFormation template creates a simple web application (WordPress),
and requires the following parameters:

- KeyName - Name of a pre-created SSH Key, you may create this manually.
- InstanceType - Instance type to use, i.e. t2.small.
- AmiId - AMI ID to use, this template has been successfully tested with the
  following amazon linux 'amzn-ami-hvm-2017.09.0.20170930-x86_64-gp2'
  aka (ami-e689729e) in us-west-2 region.
- SubnetId - Subnet ID that was created in CF1
- VpcId - VPC ID that was created in CF1
- AllowedIp - Your public IP Address to allow HTTP access to in CIDR format
- DBUser - Database Username
- DBPassword - Database Password

Outputs are:

- URL - The URL of the resulting Application
- InstanceId - The ID of the resulting Instance
- SecurityGroupId - The ID of the resulting SecurityGroup

## Python "Wrapper" / CLI

The python command-line tool you are requested to create should take in
the following parameters:

Logic Related Parameters:
- VpcCidrBlock
- SubnetCidrBlock
- KeyName
- AmiId
- InstanceType
- AllowedIp
- DBUser
- DBPassword
- OutputFileName

AWS Related Parameters:
- AwsApiId
- AwsRegion
- AwsApiKey
- VpcTemplatePath
- AppTemplatePath

Any other required information should be derived from stack outputs.

You can use any auxiliary python library you are comfortable with, design
the code structure as you see fit.

After deployment is successfully completed, this tool must print out relevant
information such as:
- DNS Name of the application
- Instance ID That was created
- Anything else you might think is relevant for the user of this tool

In addition to printing the above to STDOUT, also generate a JSON file named
according to OutputFileName parameter, and represent the data in JSON format.

Example:

```bash
> python ./tool.py --vpc-cidr-block 10.0.0.0/21 --subnet-cidr-block 10.0.0.0/24
--key-name MyKey --ami-id ami-e689729e --instance-type t2.micro
--allowed-ip 1.1.1.1/32 --db-user admin --db-password q1w2e3r4 --output-file-name deployment_1
--aws-api-id AKIAIOSFODNN7EXAMPLE --aws-api-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
--aws-region us-west-2 --vpc-template-path ./CF1-VPC.json --app-template-path ./CF2-WebApplication.json

Deployment Successful
    Application URL: <URL>
    VPC ID: <VpcId>
    Instance ID: <InstanceId>
    ..
    ..

> cat ./deployment_1.json
{
    "url": "<URL>",
    "vpc_id": "<VpcId",
    "instance_id": "<InstanceId>"
    ..
    ..
}
```

## Additional References
- Boto3 Documentation - https://boto3.readthedocs.io/en/latest/
- For more info about Free Tier accounts: https://aws.amazon.com/free/
