FROM python:3.13-slim
COPY --from=docker.io/astral/uv:0.8.3 /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && apt-get install -y gettext

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY locales/ ./locales/
RUN msgfmt -o locales/pl/LC_MESSAGES/base.mo locales/pl/LC_MESSAGES/base.po
RUN msgfmt -o locales/en/LC_MESSAGES/base.mo locales/en/LC_MESSAGES/base.po

COPY *.py *.json ./

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
