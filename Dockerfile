# Stage 1: The Builder - Installs dependencies into a virtual environment
FROM python:3.10 as builder

WORKDIR /usr/src/app

# Install build-time system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Copy requirements and install Python packages
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: The Final Image - A lightweight image for running the application
FROM python:3.10-slim

WORKDIR /app

# Install only the necessary runtime system dependencies (for pdf2image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-built virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy all your Python source code into the container
COPY . .

# Activate the virtual environment for the CMD instruction
ENV PATH="/opt/venv/bin:$PATH"

# Set the command to run your main script when the container starts
CMD ["python", "main.py"]