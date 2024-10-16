import asyncio
import boto3
import os
import time
from binance import AsyncClient, BinanceSocketManager

# Function to upload file to S3
async def upload_file_to_s3(file_path, bucket_name):
    s3 = boto3.client('s3')
    file_key = os.path.basename(file_path)
    s3.upload_file(file_path, bucket_name, file_key)
    print(f"File uploaded to S3: {file_key}")
    return True  # Assuming upload is always successful for simplicity

async def main():
    active_file_time = int(round(time.time()) / 60)
    new_local_data_file_path = '/tmp/' + str(int(active_file_time * 60)) + '.tsv'
    bucket_name = 'binance33'  # Set your S3 bucket name

    f = open(new_local_data_file_path, 'w')
    client = await AsyncClient.create()
    bm = BinanceSocketManager(client)
    trade_socket = bm.trade_socket('BTCUSDT')

    try:
        async with trade_socket as tscm:
            while True:
                res = await tscm.recv()
                new_file_time = int(res['T'] / (1000 * 60))

                if new_file_time != active_file_time:
                    f.close()
                    upload_success = await upload_file_to_s3(new_local_data_file_path, bucket_name)
                    if upload_success:
                        print(f"Successful upload: {new_local_data_file_path}")
                        break  # This exits the loop after the first successful upload

                    # Prepare for new file if loop continues
                    active_file_time = new_file_time
                    new_local_data_file_path = '/tmp/' + str(int(active_file_time * 60)) + '.tsv'
                    f = open(new_local_data_file_path, 'w')

                # Write data to file as usual
                timestamp = str(res['T'])
                maker = '1' if res['m'] else '0'
                line = f"{res['t']}\t{res['s']}\t{res['p']}\t{res['q']}\t{timestamp}\t{maker}\n"
                f.write(line)
                print(line)
    finally:
        await client.close_connection()
        if not f.closed:
            f.close()

    return "Process completed successfully with status 200"

# Define the Lambda handler function
def lambda_handler(event, context):
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(main())
    return {
        'statusCode': 200,
        'body': result
    }
