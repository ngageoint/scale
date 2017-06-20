
.. _architecture_messaging:

Messaging System
========================================================================================================================

Scale uses a message passing interface to minimize direct communication between internal support processes (pre and post tasks)
and the authoritative PostgreSQL database. This enables high job volume while limiting database connections
to a small number of workers responsible for persisting system state.

We presently support two message brokers within Scale: Amazon SQS and RabbitMQ. RabbitMQ is deployed by default when installing
from the DCOS Universe package. While this will get you up and running quickly, it should never be relied on for a production cluster.
Our general recommendation is to use Amazon SQS, as this will require the least maintenence.

Scale is configured for your chosen message broker by the SCALE_BROKER_URL environment variable. This variable is provided in the format:

transport://[userid:password@]hostname[:port]//

Specific examples of this format will be given for each message broker below. SCALE_QUEUE_NAME variable is used to modify the default queue name
of 'scale-command-messages' used by Scale and applies to all message brokers.

Amazon SQS

Using Amazon SQS requires the following prerequisites to use within Scale:

- Identified region for SQS (us-east-1, us-west-1, etc.)
- SQS queue created within the above region
- IAM Policy with full access to above queue
- Either API Keys or an EC2 instance with IAM Role that have above IAM Policy attached

The following sample IAM Policy file would provide complete access to the scale-command-messages SQS:

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
                "arn:aws:sqs:us-east-1:*:scale-command-messages"
            ]
        }
    ]
}

If you are using API keys the Access Key and Secret Key will be placed in the userid and password placeholders respectively. When using IAM roles,
this section can be entirely omitted.

API Keys:

sqs://accesskey:secretkey@us-east-1//

IAM Roles:

sqs://us-east-1//

