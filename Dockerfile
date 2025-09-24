FROM public.ecr.aws/lambda/python:3.11 as base
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy the shopping list into the container
COPY requirements.txt .

# Install all the libraries from the list.
# --no-cache-dir is a best practice to keep the image smaller.
RUN pip install -r requirements.txt --no-cache-dir

# === processImage Stage ===
FROM base as processImage
COPY handler.py .
CMD [ "handler.process_image" ]

# === createGuestSession Stage (for our next function) ===
FROM base as createGuestSession
COPY handler.py . 
CMD [ "handler.create_guest_session" ]
