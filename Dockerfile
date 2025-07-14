FROM python:3.12-slim

# Define env vars
#ARG DECRYPTION_MASTER_KEY
#ARG PASSWORD_SALT_BASE64
ARG SERVER_IP_ADDR
ARG SERVER_URL=7233
ARG NAMESPACE=default
ARG TIME_ZONE=Etc/UTC
#ARG CRON_SCHEDULE=
ARG QUEUE_NAME=REASORS_COUPON_CLIPPER_TASK_QUEUE
ARG START_WORKFLOW=false

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SERVER_IP_ADDR=${SERVER_IP_ADDR}
ENV SERVER_PORT=${SERVER_PORT}
ENV NAMESPACE=${NAMESPACE}
ENV TIME_ZONE=${TIME_ZONE}
#ENV CRON_SCHEDULE=${CRON_SCHEDULE}
ENV QUEUE_NAME=${QUEUE_NAME}
ENV START_WORKFLOW=${START_WORKFLOW}

# Install SQLite dependencies
RUN apt-get update
RUN apt-get install -y --no-install-recommends sqlite3  \
    && apt-get autoremove -y  \
    && apt-get clean -y  \
    && rm -rf /var/lib/apt/lists/*

## Set the working directory
#WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Default command runs worker and keeps it alive
CMD ["python", "run_worker_and_workflow.py"]