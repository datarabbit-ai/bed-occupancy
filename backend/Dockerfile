FROM python:3.13-slim
LABEL authors="wiktor"

# Select container's working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get upgrade -y
    # build-essential \
    # curl \
    # software-properties-common \
    # git \
#    && rm -rf /var/lib/apt/lists/*
RUN pip3 install setuptools

COPY requirements.txt .

# Install python dependencies
RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install -r requirements.txt
RUN pip3 install "fastapi[standard]"

COPY *.py ./

EXPOSE 8000

CMD ["fastapi", "run", "main.py"]
