FROM python:3.12.12

WORKDIR /app
COPY . .


ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y libpq-dev build-essential
RUN pip install --upgrade pip && pip install --no-cache-dir -r ./requirements.txt


ENTRYPOINT ["python"]
CMD ["-m", "jarvis_botz.app"]

