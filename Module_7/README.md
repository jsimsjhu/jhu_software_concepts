# Module 7 – AWS S3 & SageMaker

This module demonstrates:
- AWS S3 bucket creation and file upload
- SageMaker notebook instance setup
- Data download from S3 to SageMaker
- EC2 deployment with Docker Compose

## Prerequisites

- AWS account with IAM user `dailyWork-JS`
- MFA enabled
- Python 3.11+
- Docker Desktop

## Files

- `src/s3_fetch.py` – boto3 logic to download from S3
- `grad-cafe-pipeline.ipynb` – Jupyter notebook for data processing
- `ec2/docker-compose.ec2.yml` – Docker Compose for EC2 deployment

## AWS Resources Created

- S3 bucket: `grad-cafe-bucket`
- SageMaker notebook instance: `dailyWork-JS`
- EC2 instance: `module-7-ec2`

## Deployment Steps

1. Upload `applicant_data.json` to S3 bucket
2. Launch SageMaker notebook instance
3. Run notebook to download and process data
4. Deploy Flask app on EC2 using Docker Compose

## Screenshots

- `AWS-MFA-Screenshot.png` – MFA enabled
- `IAM_Screenshot.png` – IAM user created
- `grad-cafe-bucket.png` – S3 bucket with data
- `liveNotebook.png` – SageMaker notebook running
- `ec2-instance.png` – EC2 instance details
- `ec2-security-group.png` – Security group rules
- `ec2-compose-ps.png` – Docker Compose services
- `ec2-app.png` – Flask app running on EC2