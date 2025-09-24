import boto3
import os
import json
import logging
import datetime
import uuid
from decimal import Decimal

# ======================================================================================
# SETUP & CONFIGURATION
# ======================================================================================

# Configure logging to be clear and informative in CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients once per container reuse for performance
s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')

# Get table names from environment variables set in serverless.yml
PHOTOS_TABLE = os.environ.get('PHOTOS_TABLE', 'Photos')
WEDDINGS_TABLE = os.environ.get('WEDDINGS_TABLE', 'Weddings')
SESSIONS_TABLE = os.environ.get('SESSIONS_TABLE', 'GuestSessions')

photos_table = dynamodb.Table(PHOTOS_TABLE)

# ======================================================================================
# LAMBDA HANDLER: process_image
# This function is triggered when a new photo is uploaded to S3.
# ======================================================================================

def process_image(event, context):
    """
    Analyzes an uploaded wedding photo, indexes faces in Rekognition,
    and stores the metadata in DynamoDB.
    """
    logger.info("## EVENT RECEIVED")
    logger.info(json.dumps(event))

    # 1. Get the bucket and key (filename) from the S3 event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    image_key = event['Records'][0]['s3']['object']['key']
    
    # Assumption: The WeddingID is the first part of the S3 key (the folder name)
    # e.g., for key 'gloria-steve-2025/photo123.jpg', wedding_id is 'gloria-steve-2025'
    try:
        wedding_id = image_key.split('/')[0]
        if not wedding_id:
            raise ValueError("WeddingID could not be determined from S3 key.")
    except (IndexError, ValueError) as e:
        logger.error(f"Failed to parse WeddingID from key '{image_key}': {e}")
        return {'statusCode': 400, 'body': 'Invalid S3 key format'}

    # 2. Call Rekognition to index the faces
    # The CollectionID in Rekognition MUST match our WeddingID
    try:
        logger.info(f"Indexing faces for {image_key} in collection {wedding_id}...")
        response = rekognition_client.index_faces(
            CollectionId=wedding_id,
            Image={'S3Object': {'Bucket': bucket_name, 'Name': image_key}},
            ExternalImageId=image_key,  # We use the S3 key as the external ID for easy reference
            DetectionAttributes=['ALL']
        )
        logger.info("## REKOGNITION RESPONSE")
        logger.info(json.dumps(response, default=str))

    except rekognition_client.exceptions.ResourceNotFoundException:
        logger.error(f"Rekognition collection '{wedding_id}' does not exist.")
        # Here you might add logic to auto-create the collection if desired
        return {'statusCode': 404, 'body': f"Collection '{wedding_id}' not found."}
    except Exception as e:
        logger.error(f"Error calling Rekognition IndexFaces: {e}")
        # We could update DynamoDB with a 'FAILED' status here
        return {'statusCode': 500, 'body': 'Rekognition processing failed.'}
        
    # 3. Prepare the data for our DynamoDB 'Photos' table
    face_records = response.get('FaceRecords', [])
    face_ids = [face['Face']['FaceId'] for face in face_records]
    
    timestamp = datetime.datetime.utcnow().isoformat()

    item = {
        'ImageKey': image_key,
        'WeddingID': wedding_id,
        'Status': 'COMPLETED',
        'ProcessedTimestamp': timestamp,
        'FaceCount': len(face_records),
        'FaceIDs': face_ids if face_ids else None, # Store FaceIDs if any were found
        'RekognitionDetails': json.loads(json.dumps(response.get('FaceRecords', []), default=str)) # Store rich metadata
    }

    # 4. Write the item to DynamoDB
    try:
        logger.info(f"Writing item to DynamoDB Photos table: {item}")
        photos_table.put_item(Item=item)
        logger.info("Successfully wrote metadata to DynamoDB.")
    except Exception as e:
        logger.error(f"Error writing to DynamoDB: {e}")
        return {'statusCode': 500, 'body': 'Database write failed.'}

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Image processed successfully',
            'imageKey': image_key,
            'facesDetected': len(face_records)
        })
    }


# ======================================================================================
# LAMBDA HANDLER: create_guest_session (We will build this next)
# ======================================================================================
def create_guest_session(event, context):
    # TODO: Logic for handling guest selfie upload will go here
    pass

# ======================================================================================
# LAMBDA HANDLER: get_session_results (We will build this next)
# ======================================================================================
def get_session_results(event, context):
    # TODO: Logic for fetching matched photos for a session will go here
    pass