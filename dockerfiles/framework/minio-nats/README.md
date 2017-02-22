[![build status](https://gitlab.balldayton.com/ball-docker/minio-nats/badges/master/build.svg)](https://gitlab.balldayton.com/ball-docker/minio-nats/commits/master)

Minio and NATS
==============
An image containing minio and NATS streaming server setup as an S3/SQS analog.

Running this image will server SQS compatible messages via NATS streaming server on port 4222 and minio on port 9000.
This setup is quite useful for developing S3 enabled applications.
Also included is a platform independent (pure python) wheel for the pynats library which can be used to subscribe to the NATS events.
It should work on python 2 or python 3. [https://github.com/mcuadros/pynats]
If you are using Python 3 asyncio, it is recommended that you use the official ansyncio client [https://github.com/nats-io/asyncio-nats].
The `mc` minio CLI is available in the docker image. It can also be downloaded here: [https://minio.io/downloads/#minio-client]

Usage
-----
1. Run the docker image:```
ACCESS_KEY=$(openssl rand -base64 12)
SECRET_KEY=$(openssl rand -base64 24)
docker run -d -p 9000:9000 -p 4222:4222 -e "MINIO_ACCESS_KEY=$ACCESS_KEY" -e "MINIO_SECRET_KEY=$SECRET_KEY" geoint/minio-nats
# use this for a local docker
MINIO_URL=http://localhost:9000
NATS_URL=nats://localhost:4222
# use this if using docker-machine to run docker in a VM
MINIO_URL=http://$(docker-machine ip default):9000
NATS_URL=nats://$(docker-machine ip default):4222
```

1. Configure the minio client for auth: `mc config host add myminio $MINIO_URL $ACCESS_KEY $SECRET_KEY`
1. Create a bucket: `mc mb myminio/mybucket`
1. Add an event notifier to the bucket: `mc events add myminio/mybucket arn:minio:sqs:us-east-1:1:nats --suffix .jpg`
1. Verify the event notifier: `mc events list myminio/mybucket`
1. Run `./test.py $NATS_URL &` and add a file to the bucket to verify the setup: `mc cp Blank.jpg myminio/mybucket`
