FROM python:3.9

WORKDIR /app

RUN apt-get -y update

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY app.py .

EXPOSE 80

CMD ["python3", "./app.py"]
