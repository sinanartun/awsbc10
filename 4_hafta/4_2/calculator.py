import json

def lambda_handler(event, context):
    # Extract parameters from the event
    action = event.get("action")
    var1 = event.get("var1")
    var2 = event.get("var2")

    # Check if var1 and var2 are numbers
    try:
        var1 = float(var1)
        var2 = float(var2)
    except (TypeError, ValueError):
        return {
            'statusCode': 400,
            'body': json.dumps("Invalid input: var1 and var2 must be numbers")
        }

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
