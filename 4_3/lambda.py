import mysql.connector
import os

def lambda_handler(event, context):
    # Extract bucket name and file key from the S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Connect to RDS
    try:
        conn = mysql.connector.connect(
            host=os.environ['RDS_HOST'],
            user=os.environ['RDS_USER'],
            password=os.environ['RDS_PASSWORD'],
            database=os.environ['RDS_DB'],
            port=os.environ['RDS_PORT'],
            connect_timeout=5
        )
    except mysql.connector.Error as e:
        print("ERROR: Unexpected error: Could not connect to MySQL instance.")
        print(e)
        return "Error"

    print("SUCCESS: Connection to RDS MySQL instance succeeded")

    # Format the S3 path
    s3_path = f"s3://{bucket}/{key}"

    # Perform SQL operation
    try:
        cursor = conn.cursor()
        sql_statement = f"LOAD DATA FROM S3 '{s3_path}' INTO TABLE binance.BTCUSDT FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' (bid, parameter, price, quantity, time, maker);"
        cursor.execute(sql_statement)
        conn.commit()
        cursor.close()
    except mysql.connector.Error as e:
        print("ERROR: Could not execute SQL statement.")
        print(e)
    finally:
        conn.close()

    return 'Success!'
