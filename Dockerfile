FROM python:3.9-slim

# Install system dependencies for OpenCV and GLib
RUN apt-get update && apt-get install -y libglib2.0-0 libgl1-mesa-glx

# Set the working directory
WORKDIR /app

# Copy the content of the current directory to the /app directory in the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run your bot (adjust to your actual script)
CMD ["python", "main.py"]
