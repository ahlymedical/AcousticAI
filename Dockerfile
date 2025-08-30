# Use an official Python runtime as a parent image
FROM python:3.9

# Install ffmpeg which is required for audio file conversion
RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Set the cache directory for Spleeter models
ENV SPLEETER_MODEL_PATH=/app/spleeter_models

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# --- THIS IS THE CRUCIAL LINE ---
# Download and cache the Spleeter models during the build process
RUN python -c "from spleeter.separator import Separator; Separator('spleeter:2stems')"

# Copy the rest of your app's code into the container
COPY . .

# Set the command to run your app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "300", "app:app"]
