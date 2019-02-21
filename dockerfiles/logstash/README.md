# Logstash - Scale
Logstash image loaded with custom configurations to support log capture within Scale.

## Configuration
This image provides a number of environment variables that can be used to tweak the behavior of logstash.

* ELASTICSEARCH_URLS: Comma delimited IP or DNS addresses serving the Elasticsearch API. Production deployments of Elasticsearch should be fronted with a load balancer. In this case, a single value should be provided.
* LOGSTASH_ARGS: String of any arbitrary command-line arguments to pass to Logstash.
* LOGSTASH_DEBUG: Case-sensitive boolean value indicating whether to output incoming messages to stdout. Must be `true` if output is desired, any other value will not output messages.
* TEMPLATE_URI: URL to container accessible location of Logstash template config. See below for example.

### Logstash Configuration Template
If there is a need to override the default configuration or specify additional filters, the following example contains
the minimum required configuration that should be used as a starting point for your config.

```
input {
  http {
    port => 80
    type => "app-healthcheck"
  }
}
filter {
  if [type] == "app-healthcheck" {
    drop { }
  }
}
output {
  elasticsearch {
    hosts => _ES_HOSTS_
  }
}
```

The `http` input handler and `filter` is needed to support Marathon health checks and drop all messages from that input.
If health checks are not needed all that is required is the `output` directive. The `_ES_HOSTS_` value is required to
support the configuration of Elasticsearch nodes into the Logstash pipeline.
