# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Force rebuild comment: 2025-10-30

# Copy the rest of the application code into the container
COPY . .

# Command to run the application using Gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
