import boto3

def create_rekognition_collection(collection_id):
    """
    Creates an Amazon Rekognition collection.
    
    :param collection_id: The ID for the collection to be created.
    """
    client = boto3.client('rekognition')
    
    try:
        response = client.create_collection(CollectionId=collection_id)
        print(f"Collection '{collection_id}' created successfully.")
        print(f"Status code: {response['StatusCode']}")
        return response
    except client.exceptions.ResourceAlreadyExistsException:
        print(f"Collection '{collection_id}' already exists. No action taken.")
    except Exception as e:
        print(f"Error creating collection: {e}")

if __name__ == '__main__':
    # We'll use the WeddingID as our CollectionID
    wedding_id = "gloria-steve-2025"
    create_rekognition_collection(wedding_id)