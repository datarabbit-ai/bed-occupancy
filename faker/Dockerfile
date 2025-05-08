FROM python:3.13-slim
LABEL authors="wiktor"

# Select container's working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get upgrade -y
RUN mkdir "../db"

COPY requirements.txt .

# Install python dependencies
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY *.py ./

CMD ["python3", "seed_data.py"]
