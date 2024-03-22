FROM python:3.8-buster 

WORKDIR /app


ENV FLASK_ENV=dev

RUN apt-get update && apt-get install -y curl

RUN sh -c "curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -" \
    && apt-get update \
    && sh -c "curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list" \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && ACCEPT_EULA=Y apt-get install -y mssql-tools18

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential git libssl-dev libffi-dev python3-dev xmlsec1 libxmlsec1 libxmlsec1-dev libxmlsec1-openssl unixodbc-dev 
    
RUN pip install --upgrade pip

COPY ./src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
ENV PYTHONPATH "/app/src"

EXPOSE 5000


CMD ["gunicorn", "-w 2", "--timeout", "6000", "-b :5000", "app:create_app()", "--preload"]


