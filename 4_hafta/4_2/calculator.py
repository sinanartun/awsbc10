import json

def lambda_handler(event, context):
    # Extract parameters from the event
    action = event["queryStringParameters"]["action"]
    var1 = event["queryStringParameters"]["var1"]
    var2 = event["queryStringParameters"]["var2"]

    # Check if var1 and var2 are numbers

    var1 = int(var1)
    var2 = int(var2)
    print("var1",var1)
    print("var2", var2)


    # Perform action based on the action parameter
    if action == "add":
        result = var1 + var2
    elif action == "sub":
        result = var1 - var2
    elif action == "multiply":
        result = var1 * var2
    elif action == "divide":
        # Handle division by zero
        if var2 == 0:
            return {
                'statusCode': 400,
                'body': json.dumps("Error: Division by zero is not allowed")
            }
        result = var1 / var2
    else:
        return {
            'statusCode': 400,
            'body': json.dumps("Invalid action: action must be 'add', 'sub', 'multiply', or 'divide'")
        }

    # Return the result as a JSON response
    return {
        'statusCode': 200,
        'body': json.dumps({'result': result})
    }
