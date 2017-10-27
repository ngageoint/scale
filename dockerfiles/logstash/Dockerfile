ARG IMAGE=logstash:2.4-alpine
FROM $IMAGE
MAINTAINER Scale Developers "https://github.com/ngageoint/scale"

LABEL \
    RUN="docker run -e ELASTICSEARCH_URLS=http://elastic:9200 -p 8000:8000 -p 80:80 geoint/scale-logstash" \
    SOURCE="https://github.com/ngageoint/scale/tree/master/dockerfiles/logstash" \
    DESCRIPTION="Log aggregator, formatter and Elasticsearch forwarder for Scale jobs" 

RUN apk add --no-cache supervisor py-requests

COPY supervisord.conf /etc/supervisord.conf

RUN mkdir -p /opt/watchdog && chown -R logstash /opt/watchdog && chown logstash /var/run
COPY logstash.conf-template /opt/logstash/logstash.conf-template
COPY elastic_watchdog.py /opt/logstash/elastic_watchdog.py

CMD [ "supervisord" ]

