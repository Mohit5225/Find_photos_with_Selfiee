# === base stage ===
FROM public.ecr.aws/lambda/python:3.11 as base

# Set working directory inside Lambda environment
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy the requirements file from the nested location
# NOTE: Assumes the correct requirements.txt is inside the 'rekognition' folder
COPY server/Find_photos_with_Selfiee/rekognition/requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt --no-cache-dir

# === processimage stage ===
FROM base as processimage

# Copy the handler file from its nested location
COPY server/Find_photos_with_Selfiee/rekognition/handler.py .

# Specify the Lambda handler
CMD [ "handler.process_image" ]

# === createguestsession stage ===
FROM base as createguestsession

# Copy the handler file again for the other function
COPY server/Find_photos_with_Selfiee/rekognition/handler.py .

# Specify the Lambda handler for guest session
CMD [ "handler.create_guest_session" ]
