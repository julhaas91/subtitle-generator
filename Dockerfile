FROM python:3.9-slim

ENV PYTHONUNBUFFERED True

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY src ./src

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 src.main:app
