FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get upgrade -y

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY *.py ./
COPY *.json ./

EXPOSE 8000

CMD ["fastapi", "run", "main.py"]
