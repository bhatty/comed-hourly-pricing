# Use an official Python slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create a log file to avoid errors if the app tries to write to it
RUN touch comed_monitor.log && chmod 666 comed_monitor.log

# Command to run the monitor
CMD ["python", "main.py", "--monitor"]
