FROM python:3.9

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV AWS_REGION="us-west-2" \
    VPC_CIDR_BLOCK="10.0.0.0/21" \
    SUBNET_CIDR_BLOCK="10.0.0.0/24" \
    TEMPLATE_S3_BUCKET="intuit-onsite2023" \
    VPC_TEMPLATE_S3_KEY="CF1-VPC.json" \
    APP_TEMPLATE_S3_KEY="CF2-WebApplication.json" \
    KEY_NAME="IntuitOnsite" \
    INSTANCE_TYPE="t2.micro" \
    AMI_ID="ami-e689729e"\
    ALLOWED_IP="0.0.0.0/0" \
    DB_USER=admin \
    DB_PASSWORD="q1w2e3r4" \
    OUTPUT_FILE_NAME="deployment_1" \
    DELETE=False

ENTRYPOINT ["python", "app.py"]