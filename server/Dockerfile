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

RUN mkdir -p /app/server
WORKDIR /app/server

# For debugging
RUN pip install \
    django-debug-toolbar \
    django-extensions \
    flake8 \
    ipdb \
    ipython

COPY requirements.txt .
RUN pip install -r requirements.txt

CMD python manage.py runserver
