ARG IMAGE=fluent/fluentd:v1.4-1
FROM $IMAGE

MAINTAINER Scale Developers "https://github.com/ngageoint/scale"

LABEL \
    RUN="docker run -e ELASTICSEARCH_URL=http://elasticsearch:9200 -p 24224:24224 -p 24220:24220 geoint/scale-fluentd" \
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
 
RUN apk add --no-cache --update python2

COPY scripts/ /

USER fluent

COPY fluent.conf /fluentd/etc/

ENTRYPOINT ["sh", "/entrypoint.sh"]
