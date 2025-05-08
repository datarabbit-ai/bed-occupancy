FROM python:3.13-slim
LABEL authors="wiktor"

# Select container's working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get upgrade -y

COPY requirements.txt .

# Install python dependencies
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY main.py ./

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
