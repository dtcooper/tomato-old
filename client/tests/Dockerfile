FROM python:3.7

EXPOSE 9623
ENV DISPLAY=:0

ENV PGHOST db
ENV PGUSER postgres
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libnss3 \
        libsox-fmt-all \
        lxde \
        nginx \
        postgresql-client \
        sox \
        supervisor \
        x11vnc \
        xauth \
        xvfb \
    && rm -rf /var/lib/apt/lists/*

RUN wget -qO - https://github.com/novnc/noVNC/archive/v1.1.0.tar.gz \
    | tar xz --strip-components=1 -C /var/www/html

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /venv
WORKDIR /venv

# Create venv for server
COPY server/requirements.txt /tmp
RUN python -m venv --prompt server server \
    && server/bin/pip install -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY client/requirements /tmp/requirements
RUN pip install -r /tmp/requirements/base.txt -r /tmp/requirements/linux.txt \
    && rm -r /tmp/requirements

COPY client/tests/image /

WORKDIR /app/client
ENTRYPOINT /entrypoint.sh
CMD bash
