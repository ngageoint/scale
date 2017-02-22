#!/usr/bin/env python
import json
import pynats
import sys

if len(sys.argv) != 2:
    print("Please specify a nats URL nats://server:4222")
    sys.exit(-1)
print("Listening to %s" % sys.argv[1])
c = pynats.Connection(verbose=True, url=sys.argv[1])
c.connect()

def cb(msg):
    d = json.loads(msg.data)
    import pprint
    pprint.pprint(d)

c.subscribe('minio', cb)
print("Please copy the Blank.jpg to the bucket")
c.wait(count=1)
c.close()
