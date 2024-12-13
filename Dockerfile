FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

COPY config/serviceAccountKey.json /app/config/serviceAccountKey.json

CMD ["gunicorn", "run:app"]
