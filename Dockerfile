# Use an official Python runtime as a parent image
FROM python:3.9

# Install ffmpeg which is required for audio file conversion
RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Spleeter downloads models, so we need to set the cache directory
ENV SPLEETER_MODEL_PATH=/app/spleeter_models
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app's code into the container
COPY . .

# Set the command to run your app using Gunicorn
# Gunicorn is a production-ready web server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "300", "app:app"]
