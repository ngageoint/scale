FROM alpine

ENV VAULT_VERSION 0.7.0

ADD https://releases.hashicorp.com/vault/${VAULT_VERSION}/vault_${VAULT_VERSION}_linux_amd64.zip vault.zip
RUN apk add --update unzip openssl ca-certificates curl jq && \
    unzip vault.zip && \
    rm vault.zip && \
    cp vault /usr/bin && \
    apk del unzip && \
    rm -rf /var/cache/apk/*

COPY run-vault /usr/bin/run-vault
COPY config.hcl config.hcl

RUN chmod +x /usr/bin/run-vault

ENTRYPOINT ["run-vault"]
CMD ["server", "-config=config.hcl"]
