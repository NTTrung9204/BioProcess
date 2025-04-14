FROM python:3.11.7

WORKDIR /app

COPY . .

RUN pip install --upgrade pip setuptools wheel

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "run.py"]
