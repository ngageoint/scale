
.. _architecture_messaging:

================================================================================
Messaging System
================================================================================

Scale uses a message passing interface to minimize direct communication between internal support processes (pre and post tasks)
and the authoritative PostgreSQL database. This enables high job volume while limiting database connections
to a small number of workers responsible for persisting system state.

We presently support two message brokers within Scale: Amazon SQS and RabbitMQ. RabbitMQ is deployed by default when installing
from the DCOS Universe package. While this will get you up and running quickly, it should never be relied on for a production cluster.
Our general recommendation is to use Amazon SQS, as this will require the least maintenence.

*SCALE_BROKER_URL* environment variable is used by Scale to configure your chosen message broker. When left unset, RabbitMQ will be deployed alongside.
Specific examples of this format will be given for each message broker below. This variable is provided in the format:

``transport://[userid:password@]hostname[:port]//``

*SCALE_QUEUE_NAME* environment variable is used to modify the default queue name of ``scale-command-messages``. It applies to all message brokers.

--------------------------------------------------------------------------------
Amazon SQS
--------------------------------------------------------------------------------

Using Amazon SQS requires the following prerequisites to use within Scale:

- Identified region for SQS (us-east-1, us-west-1, etc.)
- SQS queue created within the above region
- IAM Policy with full access to above queue
- Either API Keys or an EC2 instance with IAM Role that have above IAM Policy attached

The following sample IAM Policy file would provide complete access to the scale-command-messages SQS:

.. code-block:: javascript
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "Stmt689276142600",
                "Effect": "Allow",
                "Action": [
                    "sqs:*"
                ],
                "Resource": [
                    "arn:aws:sqs:us-east-1:*:scale-command-message"
                ]
            }
        ]
    }

If you are using API keys the Access Key ID and Secret Access Key will be placed in the SCALE_BROKER_URL userid and password placeholders respectively. When using IAM roles,
this section can be entirely omitted. Based on the above examples your environment variables passed to Scale should be set as follows:

**API Keys:** 

SCALE_BROKER_URL: ``sqs://accesskeyid:secretaccesskey@us-east-1//``
SCALE_QUEUE_NAME: ``scale-command-message``

**IAM Roles:** 

SCALE_BROKER_URL: ``sqs://us-east-1//``
SCALE_QUEUE_NAME: ``scale-command-message``

--------------------------------------------------------------------------------
RabbitMQ
--------------------------------------------------------------------------------

Using RabbitMQ is the current option for on-premise Scale deployments. While Scale will deploy RabbitMQ automatically during launch if *SCALE_BROKER_URL* is unset,
this should never be relied on for anything beyond demonstration purposes. The default RabbitMQ deployment has no mounted persistent storage, so all messages in the
broker will be lost if there is a container restart.

Using RabbitMQ requires the following prerequisites to use within Scale:

- Running RabbitMQ 3.6+ instance
- User name and password to authenticate to RabbitMQ

The easiest route to RabbitMQ deployment would just be to deploy into Marathon alongside Scale. The following sample marathon.json would be a reasonable starting point:

.. code-block:: javascript
    {
      "id": "/rabbitmq",
      "cpus": 1,
      "mem": 512,
      "disk": 0,
      "instances": 1,
      "container": {
        "docker": {
          "image": "rabbitmq:3.6",
          "forcePullImage": true,
          "privileged": false,
          "portMappings": [
            {
              "containerPort": 5672,
              "protocol": "tcp",
              "hostPort": 5672,
              "labels": {
                "VIP_0": "/rabbitmq:5672"
              }
            },
            {
              "containerPort": 15672,
              "protocol": "tcp"
            }
          ],
          "network": "BRIDGE"
        },
        "type": "DOCKER",
        "volumes": [
          {
            "containerPath": "/var/lib/rabbitmq",
            "hostPath": "rabbitmq",
            "mode": "RW"
          },
          {
            "containerPath": "rabbitmq",
            "persistent": {
              "size": 1024
            },
            "mode": "RW"
          }
        ]
      },
      "healthChecks": [
        {
          "protocol": "TCP",
          "gracePeriodSeconds": 300,
          "intervalSeconds": 60,
          "timeoutSeconds": 20,
          "maxConsecutiveFailures": 3
        }
      ],
      "residency": {
        "relaunchEscalationTimeoutSeconds": 10,
        "taskLostBehavior": "WAIT_FOREVER"
      }
    }

The above configuration will generate a persistent storage volume (1GiB) and pin RabbitMQ to that node. This will protect you from data loss
as long as that node remains in your cluster. Setting up a truly fault tolerant RabbitMQ cluster is outside the scope of this guide.

To configure Scale to use the RabbitMQ deployed as described above we need to set environment variables as below:

SCALE_BROKER_URL: ``amqp://guest:guest@rabbitmq.marathon.mesos:5672``

*SCALE_QUEUE_NAME* can be left unset if the default ``scale-command-messages`` value is satisfactory.