FROM python:3.13-slim
COPY --from=docker.io/astral/uv:0.8.3 /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt .

RUN uv pip install --system -r requirements.txt

COPY *.py ./
COPY *.json ./

EXPOSE 8000

CMD ["fastapi", "run", "main.py"]
