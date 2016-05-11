FROM alpine
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

ADD JPL_ASTER.tar.gz /var/

# The job type definition. Don't edit this, use job_type.json or job_type.yml as this will be replaced
LABEL com.ngageoint.scale.job-type="{\"name\":\"jpl-signatures\",\"version\":\"1.0.0\",\"title\":\"JPL Signature Library\",\"description\":\"Select a signature from the JPL signature library.\",\"icon_code\":\"f012\",\"docker_image\":\"devdocker-reg.devnet.prv:5000/geoint/jpl-signatures_1.0\",\"priority\":250,\"timeout\":300,\"max_tries\":2,\"cpus_required\":0.1,\"mem_required\":25,\"interface\":{\"version\":\"1.0\",\"command\":\"./entryPoint.sh\",\"command_arguments\":\"$ {signature_name} $ {job_output_dir}\",\"input_data\":[{\"name\":\"signature_name\",\"type\":\"property\",\"required\":true}],\"output_data\":[{\"name\":\"signature\",\"type\":\"file\",\"required\":true}]}}"
###

RUN adduser -u 1001 -D  scale
COPY entryPoint.sh ./
ENTRYPOINT ["./entryPoint.sh"]
