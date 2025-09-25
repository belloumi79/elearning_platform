FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Firebase credentials are no longer used; removed COPY of serviceAccountKey.json

CMD ["gunicorn", "run:app"]
