FROM logstash:2.4
MAINTAINER Jonathan Meyer <jon@gisjedi.com>

RUN apt-get update && apt-get install -y supervisor python-requests

COPY supervisord.conf /etc/supervisord.conf

RUN mkdir -p /opt/watchdog && chown -R logstash /opt/watchdog && chown logstash /var/run
COPY logstash.conf-template /opt/watchdog/logstash.conf-template
COPY elastic_watchdog.py /opt/watchdog/elastic_watchdog.py

CMD [ "supervisord" ]

