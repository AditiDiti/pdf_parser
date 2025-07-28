FROM --platform=linux/amd64 python:3.10

# Set working directory inside the container
WORKDIR /app

# Copy main script and requirements into the container
COPY main.py .
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run your script when container starts
CMD ["python", "main.py"]
