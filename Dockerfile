FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --create-home --uid 10001 agent \
    && mkdir -p /app/data /app/logs \
    && chown -R agent:agent /app

USER agent

CMD ["python", "-m", "app.bot"]
