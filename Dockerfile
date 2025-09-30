FROM python:3.13-alpine3.22

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py"]