# Fluentd - Scale
Fluentd image loaded with custom configurations to support log capture within Scale.

This image provides environment variables that can be used to manipulate the behavior of the log forwarder.

* ELASTICSEARCH_URLS: Comma delimited IP or DNS addresses serving the Elasticsearch API. Production deployments of Elasticsearch should be fronted with a load balancer. In this case, a single value should be provided.
* TEMPLATE_URI: URL to container accessible location of fluentd config. See below for example.
