
.. _architecture_logs:

ElasticSearch Logs
========================================================================================================================

Scale stores its logs in an ElasticSearch database. You can perform REST API calls to retrieve log information from
ElasticSearch. To retrieve logs in correct order, you should order first by *@timestamp* ascending and then by
*scale_order_num* ascending. Scale stores its logs in a JSON format with the following fields:

**message**: JSON string

    The log message

**@timestamp**: JSON string

    The ISO-8601 timestamp marking when the message was logged

**scale_order_num**: JSON number

    A sequence number used to indicate correct log message order when multiple messages share the same *@timestamp*
    value. To retrieve logs in correct order, you should order first by *@timestamp* ascending and then by
    *scale_order_num* ascending.

**scale_task**: JSON string

    The ID of the Scale task that produced this log message

**scale_job_exe**: JSON string

    The ID of the Scale job execution that produced this log message

**scale_node**: JSON string

    The host name of the Scale node that executed the Scale task

**stream**: JSON string

    Indicates which stream produced the log message, either "stdout" or "stderr"
