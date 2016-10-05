# Logstash Elastic High-Availability
Image to support Scale log capture with Logstash failover between Elasticsearch nodes.

This image is primarily intended to mitigate issues when Elasticsearch cluster nodes fail and are instantiated
elsewhere. Barring all nodes moving to other addresses, the watchdog process will discover the new locations from
Elasticsearch APIs and update the logstash pipeline to all available nodes.

## Configuration
This image provides a number of environment variables that can be used to tweak the behavior of logstash.

* ELASTICSEARCH_URLS: One or more comma delimited full URLs to Elasticsearch nodes to bootstrap watchdog. For example,
 "http://node01:9200,http://node02:9200". The watchdog will continually update Logstash configuration as nodes are 
 added or removed.
* LOGSTASH_ARGS: String of any arbitrary command-line arguments to pass to Logstash.
* SLEEP_TIME: Time in seconds to sleep between watchdog checks of Elasticsearch nodes.
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
support the watchdog injection of nodes into the Logstash pipeline.