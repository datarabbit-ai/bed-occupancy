FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    gettext

COPY requirements.txt .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY locales/ ./locales/
RUN mkdir -p locales/en/LC_MESSAGES locales/pl/LC_MESSAGES
RUN msgfmt -o locales/pl/LC_MESSAGES/base.mo locales/pl/LC_MESSAGES/base.po
RUN msgfmt -o locales/en/LC_MESSAGES/base.mo locales/en/LC_MESSAGES/base.po

COPY main.py agent.py *.json ./

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
