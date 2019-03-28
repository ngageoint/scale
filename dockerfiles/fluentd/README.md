# Fluentd - Scale
Fluentd image loaded with custom configurations to support log capture within Scale.

We require a single environment variable to configure the backing Elasticsearch cluster. `ELASTICSEARCH_URL` accepts a single URL serving the Elasticsearch API.
Production deployments of Elasticsearch should be fronted with a load balancer to satisfy this requirement.

Supported example settings for `ELASTICSEARCH_URL`:

- "http://192.168.1.10"
- "http://192.168.1.10:9200"
- "https://elastic.example.com"
- "https://username@password:elastic.example.com"