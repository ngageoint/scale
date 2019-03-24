ARG IMAGE=fluent/fluentd:v1.4-onbuild-1
FROM $IMAGE

MAINTAINER Scale Developers "https://github.com/ngageoint/scale"

LABEL \
    RUN="docker run -e ELASTICSEARCH_URLS=http://elastic:9200 -p 8000:8000 -p 80:80 geoint/scale-fluentd" \
    SOURCE="https://github.com/ngageoint/scale/tree/master/dockerfiles/fluentd" \
    DESCRIPTION="Log aggregator, formatter and Elasticsearch forwarder for Scale jobs" 

USER root

RUN apk add --no-cache --update --virtual .build-deps \
        build-base ruby-dev \
 && gem install \
        fluent-plugin-elasticsearch \
 && gem sources --clear-all \
 && apk del .build-deps \
 && rm -rf /home/fluent/.gem/ruby/2.5.0/cache/*.gem

USER fluent
