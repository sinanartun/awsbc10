import json
import boto3
import pandas as pd
import joblib
import os
import numpy as np
from sklearn.exceptions import NotFittedError

bucket_name = os.environ['BUCKET_NAME']
remote_model_key = os.environ['REMOTE_KEY']
local_model_key = f"/tmp/{remote_model_key}"

def lambda_handler(event, context):
    # CORS handling
    origin = event['headers'].get('origin', '')

    # Validating and extracting query parameters
    query_params = event.get("queryStringParameters", {})
    required_params = ["model", "yil", "km", "renk"]

    if not all(param in query_params for param in required_params):
        return {"statusCode": 400, "body": "Missing required query parameters"}

    try:
        model = query_params["model"]
        yil = int(query_params["yil"])
        km = int(float(query_params["km"]))  # Handle both int and float inputs
        renk = query_params["renk"]
    except ValueError:
        return {"statusCode": 400, "body": "Invalid parameter types"}

    # Load model
    if not os.path.exists(local_model_key):
        boto3.client("s3").download_file(bucket_name, remote_model_key, local_model_key)

    # Predict
    try:
        trained_model = joblib.load(local_model_key)
        input_data = pd.DataFrame([[model, yil, km, renk]], columns=["model", "yil", "km", "renk"])
        fiyat_prediction = trained_model.predict(input_data)
        fiyat = int(np.round(fiyat_prediction[0]))
    except NotFittedError:
        return {"statusCode": 500, "body": "Model not fitted"}
    except Exception as e:
        return {"statusCode": 500, "body": f"Prediction error: {str(e)}"}

    # Response
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": origin
        },
        "body": json.dumps({"fiyat": fiyat})
    }
