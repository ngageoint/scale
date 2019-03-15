ARG IMAGE=logstash:6.6.2
FROM $IMAGE
MAINTAINER Scale Developers "https://github.com/ngageoint/scale"

LABEL \
    RUN="docker run -e ELASTICSEARCH_URLS=http://elastic:9200 -p 8000:8000 -p 80:80 geoint/scale-logstash" \
    SOURCE="https://github.com/ngageoint/scale/tree/master/dockerfiles/logstash" \
    DESCRIPTION="Log aggregator, formatter and Elasticsearch forwarder for Scale jobs" 

COPY . /opt/logstash

CMD [ "sh", "/opt/logstash/entrypoint.sh" ]

