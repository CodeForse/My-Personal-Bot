# syntax=docker/dockerfile:1

FROM python:3.10

WORKDIR /app

COPY . .
RUN pip3 install -r requirements.txt

CMD [ "python", "main.py" ]