#lambda function1
import json
import boto3
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""
    
    # Get the s3 address from the Step Function event input
    key = event['s3_key']                               ## TODO: fill in
    bucket = event['s3_bucket']                         ## TODO: fill in
    
    # Download the data from s3 to /tmp/image.png
    s3.download_file(bucket, key, "/tmp/image.png")     ## TODO: fill in
    
    # We read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    # Pass the data back to the Step Function
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }


#lambda function2
import os
import io
import boto3
import json

# Fill this in with the name of your deployed model
ENDPOINT = "image-classification-2024-10-15-13-47-32-298"

# Initialize the clients for S3 and runtime
s3 = boto3.client('s3')
runtime = boto3.client('runtime.sagemaker')

def lambda_handler(event, context):
    # Parse the body to extract s3_bucket and s3_key
    if "body" in event:
        body = event["body"]
        # Check if it's a string (Lambda might pass the body as a JSON string)
        if isinstance(body, str):
            body = json.loads(body)
            
        # Extract s3_bucket and s3_key from the body
        if "s3_bucket" in body and "s3_key" in body:
            s3_bucket = body["s3_bucket"]
            s3_key = body["s3_key"]
        else:
            raise Exception("Missing 's3_bucket' or 's3_key' in the body")
    else:
        raise Exception("Missing 'body' in the event")
    
    # Fetch the image from S3
    try:
        s3_response = s3.get_object(Bucket=s3_bucket, Key=s3_key)
        image = s3_response['Body'].read()
    except Exception as e:
        raise Exception(f"Error fetching image from S3: {str(e)}")
    
    # Make a prediction using the SageMaker endpoint
    predictor = runtime.invoke_endpoint(
        EndpointName=ENDPOINT,
        ContentType='application/x-image',
        Body=image
    )
    
    # Get the prediction results and add it to the response
    body["inferences"] = json.loads(predictor['Body'].read().decode('utf-8'))
    
    # Return the response
    return {
        'statusCode': 200,
        'body': json.dumps({
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "inferences": body["inferences"]
        })
    }


#lambda function3
import json

def lambda_handler(event, context):
    # Parse the body if it's a string
    try:
        # Check if event['body'] is a string, and parse it if so
        if isinstance(event["body"], str):
            body = json.loads(event["body"])  # Parse the string to a dictionary
        else:
            body = event["body"]
        
        # Extract the inferences from the parsed body
        inferences = body["inferences"]
        
        # Confidence threshold logic
        confidence_threshold = 0.8
        high_confidence_inferences = [inf for inf in inferences if inf > confidence_threshold]
        
        # Return the response with high-confidence inferences
        return {
            'statusCode': 200,
            'body': json.dumps({
                'high_confidence_inferences': high_confidence_inferences
            })
        }
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': f"Missing key: {e}"
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }




