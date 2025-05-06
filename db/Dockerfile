FROM ubuntu
LABEL authors="wiktor"

# Select container's working directory
WORKDIR /data

# Install system dependencies
RUN apt-get update && apt-get install -y

COPY hospital.db sqlite3.exe ./
