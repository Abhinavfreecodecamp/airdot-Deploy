import boto3
from botocore.exceptions import ClientError

class minio_helper:
    def __init__(self, endpoint, access_key=None, secret_key=None, secure=True):
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            use_ssl=secure
        )
        
    def create_bucket(self, bucket_name):
        try:
            bucket = self.client.Bucket(bucket_name)
            if bucket.creation_date:
                print(f"Bucket '{bucket_name}' already exists")
            else:
                bucket.create()
                print(f"Bucket '{bucket_name}' created successfully")
        except ClientError as e:
            print(f"Error creating bucket '{bucket_name}': {e}")
    
    def delete_bucket(self, bucket_name):
        try:
            bucket = self.client.Bucket(bucket_name)
            bucket.objects.all().delete()
            bucket.delete()
            print(f"Bucket '{bucket_name}' deleted successfully")
        except ClientError as e:
            print(f"Error deleting bucket '{bucket_name}': {e}")
    
    def put_object(self, bucket, key, data):
        try:
            self.client.put_object(Bucket=bucket, Key=key, Body=data)
            return True
        except ClientError as e:
            print(f"Error putting object '{key}' to MinIO: {e}")
            return False
    
    def get_object(self, bucket, key):
        try:
            response = self.client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except ClientError as e:
            print(f"Error getting object '{key}' from MinIO: {e}")
            return None
