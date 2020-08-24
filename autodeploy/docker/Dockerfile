FROM alpine:3.12

RUN apk update && \
    apk add --no-cache jq bash curl

RUN mkdir -p /usr/autodeploy/volume
WORKDIR /usr/autodeploy

COPY autodeploy.sh .
RUN chmod +x autodeploy.sh
WORKDIR /usr/autodeploy/volume

ENTRYPOINT ["bash", "../autodeploy.sh"]
