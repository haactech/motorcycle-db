FROM python:3.11-slim

WORKDIR /app

ENV FLASK_RUN_PORT=4200

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["flask", "run", "--host=0.0.0.0"]