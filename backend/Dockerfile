FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 本番用。Cloud Run は待ち受けるポートを PORT で指定してくる(手元では 8000)
# --forwarded-allow-ips: Cloud Run の前段から届く https の情報を信用する
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --forwarded-allow-ips='*'"]
