FROM alpine
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

ADD JPL_ASTER.tar.gz /var/

# The job type definition. Don't edit this, use job_type.json or job_type.yml as this will be replaced
LABEL com.ngageoint.scale.job-type=""
###

RUN adduser -u 1001 -D  scale
COPY entryPoint.sh ./
ENTRYPOINT ["./entryPoint.sh"]
