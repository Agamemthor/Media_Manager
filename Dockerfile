# Use an official Python runtime as the base image
FROM python:3.11-slim

# Install Tcl/Tk dependencies (required for Tkinter)
RUN apt-get update && \
    apt-get install -y tcl8.6 tk8.6 && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY app/ .

# Command to run the application
CMD ["python", "media_manager.py"]
