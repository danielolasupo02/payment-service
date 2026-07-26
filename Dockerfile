FROM python:3.12-slim

WORKDIR /app

RUN useradd --create-home --uid 1000 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY gunicorn.conf.py .

USER appuser

EXPOSE 8080

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:create_app()"]
