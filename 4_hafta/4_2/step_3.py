import asyncio
import boto3
from datetime import datetime

# Helper function to download file from S3
async def download_file_from_s3(bucket_name, file_key):
    s3 = boto3.client('s3')
    download_path = f'/tmp/{file_key}'
    try:
        s3.download_file(bucket_name, file_key, download_path)
        print(f"Downloaded file {file_key} to {download_path}")
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None
    return download_path

# Function to upload the modified file back to S3 with a new file name
async def upload_file_to_s3(bucket_name, file_path, new_file_key):
    s3 = boto3.client('s3')
    new_filename = new_file_key.replace("_step_2", "")
    try:
        s3.upload_file(file_path, bucket_name, new_filename)
        print(f"Successfully uploaded {new_filename} to S3")
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None
    return new_filename

def format_data(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        print(f"Read {len(lines)} lines from {file_path}")
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    formatted_lines = []
    for idx, line in enumerate(lines):
        parts = line.strip().split('\t')
        
        # Diagnostic logging to understand the line structure
        if idx < 5:  # Print details of the first 5 lines
            print(f"Line {idx} parts: {parts}")

        if len(parts) >= 6:  # Adjusted condition to match actual line structure
            try:
                # Format quantity to 5 decimal places and price to 2 decimal places
                parts[3] = f"{float(parts[3]):.5f}"  # Quantity at index 3
                parts[2] = f"{float(parts[2]):.2f}"  # Price at index 2
                formatted_line = '\t'.join(parts)
                formatted_lines.append(formatted_line + '\n')
            except ValueError as ve:
                print(f"ValueError while formatting line: {line} - {ve}")
    
    print(f"Formatted {len(formatted_lines)} lines")
    return formatted_lines

# Main processing function for Step 3
async def process_format_and_upload_file(bucket_name, original_file_key):
    # Download the file from S3
    file_path = await download_file_from_s3(bucket_name, original_file_key)
    if not file_path:
        print("Failed to download the file, aborting.")
        return None

    # Format the data
    formatted_lines = format_data(file_path)
    if not formatted_lines:
        print("No formatted lines to write, aborting.")
        return None

    # Write the formatted data to a new file
    new_file_name = f"step_3_{original_file_key}"
    output_path = f'/tmp/{new_file_name}'
    try:
        with open(output_path, 'w') as file:
            file.writelines(formatted_lines)
            print(f"Written {len(formatted_lines)} lines to {output_path}")
    except Exception as e:
        print(f"Error writing to file {output_path}: {e}")
        return None

    # Upload the formatted file back to S3 with a new name
    upload_result = await upload_file_to_s3(bucket_name, output_path, new_file_name)
    return upload_result

# Lambda handler for Step 3
def lambda_handler(event, context):
    bucket_name = event.get('bucket_name', 'binance33')
    original_file_key = event.get('file_key', '')

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(process_format_and_upload_file(bucket_name, original_file_key))
    
    if result:
        print(f"Process completed successfully. File uploaded as {result}")
    else:
        print("Process failed.")
        
    return {
        'statusCode': 200 if result else 500,
        'file_key': result if result else "Error"
    }
