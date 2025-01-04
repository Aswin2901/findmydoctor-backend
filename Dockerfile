# Backend Dockerfile

# Use official Python image as the base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project code
COPY . /app/

# Expose port 8000 for the backend
EXPOSE 8000

# Run the Django development server
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "findmydoctor.asgi:application"]
