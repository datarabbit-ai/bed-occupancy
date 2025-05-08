FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get upgrade -y
RUN mkdir "../db"

COPY requirements.txt .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY *.py ./

CMD ["python3", "seed_data.py"]
