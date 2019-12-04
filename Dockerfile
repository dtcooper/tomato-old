FROM python:3.8

EXPOSE 8000

# Add psql
ENV PGHOST db
ENV PGUSER postgres
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app

COPY requirements requirements
RUN pip install -r requirements/base.txt -r requirements/server.txt -r requirements/dev.txt

COPY . /app
CMD python manage.py runserver
