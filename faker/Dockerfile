FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY *.py ./
COPY *.json ./

CMD ["python3", "seed_data.py"]
