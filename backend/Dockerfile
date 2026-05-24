# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install eventlet for WebSocket support
RUN pip install eventlet

# Copy the rest of the backend code into the container
COPY . .

# Hugging Face Spaces expose port 7860 by default
ENV FLASK_PORT=7860
EXPOSE 7860

# Run the application
CMD ["python", "run.py"]
