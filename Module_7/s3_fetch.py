import boto3
import os

def download_from_s3(bucket_name, object_key, local_path):
    """
    Download a file from S3 to local path.
    """
    s3 = boto3.client('s3')
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    s3.download_file(bucket_name, object_key, local_path)
    print(f"Downloaded s3://{bucket_name}/{object_key} to {local_path}")

def upload_to_s3(local_path, bucket_name, object_key):
    """
    Upload a file to S3.
    """
    s3 = boto3.client('s3')
    s3.upload_file(local_path, bucket_name, object_key)
    print(f"Uploaded {local_path} to s3://{bucket_name}/{object_key}")