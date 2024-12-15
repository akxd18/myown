# Base image (Python)
FROM python:3.9-slim

# Set working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install necessary dependencies (requests, Pillow, telebot, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the bot
CMD ["python", "main.py"]
