FROM python:3.7

EXPOSE 9623
ENV DISPLAY=:0

ENV PGHOST db
ENV PGUSER postgres
RUN apt-get update \
    && apt-get install -y \
        libsox-fmt-all \
        nginx \
        postgresql-client \
        sox \
        supervisor \
        x11vnc \
        # Remove xfce4 and purge below, can use lxde or other since linux click bug
        # exists on both
        xfce4 \
        xvfb \
    && apt-get purge -y \
        pm-utils \
        xscreensaver* \
    && rm -rf /var/lib/apt/lists/*

RUN wget -qO - https://github.com/novnc/noVNC/archive/v1.1.0.tar.gz \
    | tar xz --strip-components=1 -C /var/www/html

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /venv
WORKDIR /venv

# Create venvs for client and server
COPY server/requirements.txt /tmp
RUN python -m venv --prompt server server \
    && server/bin/pip install -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY client/requirements /tmp/requirements
RUN python -m venv --prompt client client \
    && client/bin/pip install -r /tmp/requirements/base.txt -r /tmp/requirements/linux.txt \
    && rm -r /tmp/requirements

COPY client/tests/image /

WORKDIR /app/client
ENTRYPOINT /entrypoint.sh
CMD bash
