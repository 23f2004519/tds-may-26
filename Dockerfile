FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main_q2:app", "--host", "0.0.0.0", "--port", "10000"]
