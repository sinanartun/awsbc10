import boto3
from botocore.exceptions import ClientError
import sys
import argparse
import os
from pathlib import Path

class S3Manager:
    def __init__(self, region=None, profile_name=None):
        """
        Initialize the S3Manager with optional region and AWS profile.

        :param region: AWS region, e.g., 'us-west-2'. If None, default region is used.
        :param profile_name: AWS profile name from the credentials file. If None, default profile is used.
        """
        try:
            if profile_name:
                session = boto3.Session(profile_name=profile_name, region_name=region)
            else:
                session = boto3.Session(region_name=region)
            self.s3_client = session.client('s3')
            self.s3_resource = session.resource('s3')
        except Exception as e:
            print(f"Failed to initialize S3 client: {e}")
            sys.exit(1)

    def create_bucket(self, bucket_name, region=None):
        """
        Create an S3 bucket in a specified region.

        :param bucket_name: Name of the bucket to create
        :param region: AWS region to create bucket in, e.g., 'us-west-2'
        :return: True if bucket is created, else False
        """
        try:
            if region is None or region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                location = {'LocationConstraint': region}
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration=location
                )
            print(f"Bucket '{bucket_name}' created successfully.")
            return True
        except ClientError as e:
            print(f"Failed to create bucket '{bucket_name}'.")
            print(f"Error: {e}")
            return False

    def list_buckets(self):
        """
        List all S3 buckets in the account.

        :return: List of bucket names
        """
        try:
            response = self.s3_client.list_buckets()
            buckets = [bucket['Name'] for bucket in response.get('Buckets', [])]
            print("Existing Buckets:")
            for bucket in buckets:
                print(f" - {bucket}")
            return buckets
        except ClientError as e:
            print(f"Failed to list buckets.")
            print(f"Error: {e}")
            return []

    def delete_bucket(self, bucket_name):
        """
        Delete an S3 bucket. The bucket must be empty before deletion.

        :param bucket_name: Name of the bucket to delete
        :return: True if deleted, else False
        """
        try:
            bucket = self.s3_resource.Bucket(bucket_name)
            # Ensure the bucket is empty
            bucket.objects.all().delete()
            self.s3_client.delete_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' deleted successfully.")
            return True
        except ClientError as e:
            print(f"Failed to delete bucket '{bucket_name}'.")
            print(f"Error: {e}")
            return False

    def upload_file(self, file_path, bucket_name, object_name=None):
        """
        Upload a file to an S3 bucket.

        :param file_path: Path to the file to upload
        :param bucket_name: Name of the target bucket
        :param object_name: S3 object name. If not specified, file_path's basename is used
        :return: True if file is uploaded, else False
        """
        if object_name is None:
            object_name = os.path.basename(file_path)
        try:
            self.s3_client.upload_file(file_path, bucket_name, object_name)
            print(f"File '{file_path}' uploaded to bucket '{bucket_name}' as '{object_name}'.")
            return True
        except ClientError as e:
            print(f"Failed to upload file '{file_path}' to bucket '{bucket_name}'.")
            print(f"Error: {e}")
            return False

    def download_file(self, bucket_name, object_name, file_path=None):
        """
        Download a file from an S3 bucket.

        :param bucket_name: Name of the bucket
        :param object_name: S3 object name to download
        :param file_path: Path to save the downloaded file. If not specified, uses object_name
        :return: True if file is downloaded, else False
        """
        if file_path is None:
            file_path = object_name
        try:
            self.s3_client.download_file(bucket_name, object_name, file_path)
            print(f"Object '{object_name}' from bucket '{bucket_name}' downloaded to '{file_path}'.")
            return True
        except ClientError as e:
            print(f"Failed to download object '{object_name}' from bucket '{bucket_name}'.")
            print(f"Error: {e}")
            return False

    def list_objects(self, bucket_name, prefix=None):
        """
        List objects in an S3 bucket.

        :param bucket_name: Name of the bucket
        :param prefix: Filter objects with this prefix
        :return: List of object keys
        """
        try:
            if prefix:
                response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            else:
                response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            objects = [obj['Key'] for obj in response.get('Contents', [])] if 'Contents' in response else []
            if objects:
                print(f"Objects in bucket '{bucket_name}':")
                for obj in objects:
                    print(f" - {obj}")
            else:
                print(f"No objects found in bucket '{bucket_name}'.")
            return objects
        except ClientError as e:
            print(f"Failed to list objects in bucket '{bucket_name}'.")
            print(f"Error: {e}")
            return []

    def delete_object(self, bucket_name, object_name):
        """
        Delete an object from an S3 bucket.

        :param bucket_name: Name of the bucket
        :param object_name: S3 object name to delete
        :return: True if deleted, else False
        """
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_name)
            print(f"Object '{object_name}' deleted from bucket '{bucket_name}'.")
            return True
        except ClientError as e:
            print(f"Failed to delete object '{object_name}' from bucket '{bucket_name}'.")
            print(f"Error: {e}")
            return False
        
    def sync_folder(self, folder_path, bucket_name, s3_folder=None):
        """
        Synchronize a local folder with an S3 bucket.

        :param folder_path: Path to the local folder to sync
        :param bucket_name: Name of the target S3 bucket
        :param s3_folder: S3 folder prefix. If not specified, uploads to the root of the bucket
        :return: True if synchronization is successful, else False
        """
        folder_path = Path(folder_path)
        if not folder_path.is_dir():
            print(f"The provided folder path '{folder_path}' is not a directory or does not exist.")
            return False

        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    local_file_path = Path(root) / file
                    relative_path = local_file_path.relative_to(folder_path)
                    s3_key = str(relative_path).replace(os.sep, '/')
                    if s3_folder:
                        s3_key = f"{s3_folder.rstrip('/')}/{s3_key}"
                    self.upload_file(str(local_file_path), bucket_name, object_name=s3_key)
            print(f"Folder '{folder_path}' synchronized to bucket '{bucket_name}' successfully.")
            return True
        except Exception as e:
            print(f"Failed to synchronize folder '{folder_path}' to bucket '{bucket_name}'.")
            print(f"Error: {e}")
            return False    



def main():
    bucket_name = 'deneme1111111'
    file_path = '1_hafta/1_3/s3/images'


    s3_manager = S3Manager(profile_name='default')

    
    s3_manager.create_bucket(bucket_name, region='eu-north-1')
    
    s3_manager.list_buckets()
   
    s3_manager.delete_bucket(bucket_name)
    
    s3_manager.upload_file(file_path, bucket_name, object_name='')
   
    s3_manager.download_file(bucket_name, '', file_path=file_path)
  
    s3_manager.list_objects(bucket_name, prefix='')
   
    s3_manager.delete_object(bucket_name, '')


if __name__ == "__main__":
    main()
