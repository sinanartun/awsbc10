import asyncio
import boto3
from datetime import datetime

# Helper function to download file from S3
async def download_file_from_s3(bucket_name, file_key):
    s3 = boto3.client('s3')
    download_path = f'/tmp/{file_key}'
    s3.download_file(bucket_name, file_key, download_path)
    return download_path

# Function to convert Unix time to human-readable date-time
def unix_time_to_datetime(unix_timestamp):
    return datetime.utcfromtimestamp(int(unix_timestamp) / 1000).strftime('%Y-%m-%d %H:%M:%S')

# Function to upload the processed file back to S3 with a new file name
async def upload_file_to_s3(bucket_name, file_path, new_file_key):
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket_name, new_file_key)
    return f"{new_file_key}"

# Main processing function for Step 2
async def process_and_upload_file(bucket_name, original_file_key):
    # Download the file from S3
    file_path = await download_file_from_s3(bucket_name, original_file_key)
    
    # Read the file and convert the Unix time
    with open(file_path, 'r') as file:
        lines = file.readlines()
        new_lines = []
        for line in lines:
            parts = line.split('\t')
            if len(parts) > 4:  # assuming the timestamp is the fifth element
                parts[4] = unix_time_to_datetime(parts[4])
                new_line = '\t'.join(parts)
                new_lines.append(new_line)
    
    # Write the processed data to a new file
    new_file_name = f"step_2_{original_file_key}"
    output_path = f'/tmp/{new_file_name}'
    with open(output_path, 'w') as file:
        file.writelines(new_lines)
    
    # Upload the processed file back to S3 with a new name
    upload_result = await upload_file_to_s3(bucket_name, output_path, new_file_name)
    return upload_result

# Lambda handler for Step 2
def lambda_handler(event, context):
    bucket_name = event.get('bucket_name', 'binance33')  # Default bucket name
    original_file_key = event.get('file_key', '')  # Expect the file key to be passed in the event

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(process_and_upload_file(bucket_name, original_file_key))
    return {
        'statusCode': 200,
        'file_key': result
    }
