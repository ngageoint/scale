FROM alpine:3.12

RUN apk update && \
    apk add --no-cache jq bash curl

RUN mkdir -p /usr/autodeploy
WORKDIR /usr/autodeploy

COPY autodeploy.sh /usr/autodeploy
RUN chmod +x autodeploy.sh

ENTRYPOINT ["bash", "autodeploy.sh"]