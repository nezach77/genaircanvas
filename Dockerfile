FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

COPY . webapp

RUN pip3 install -r requirements.txt

EXPOSE 80

HEALTHCHECK CMD curl --fail http://localhost:80/_stcore/health
WORKDIR /webapp

ENTRYPOINT ["streamlit", "run", "demo_app.py", "--server.port=80", "--server.address=0.0.0.0"]