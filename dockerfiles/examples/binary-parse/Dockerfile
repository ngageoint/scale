FROM alpine
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

LABEL com.ngageoint.scale.job-type="{\"name\":\"binary-parse\",\"version\":\"1.0.0\",\"title\":\"Binary File Parse\",\"description\":\"Parse arbitrary binary files extracting the date from the file metadata.\",\"author_name\":\"Trevor R.H. Clarke \\u003ctclarke@ball.com\\u003e\",\"docker_image\":\"devdocker-reg.devnet.prv:5000/geoint/parse-binary_1.0\",\"priority\":200,\"timeout\":300,\"max_tries\":1,\"cpus_required\":0.25,\"mem_required\":100,\"interface\":{\"version\":\"1.0\",\"command\":\"./parse_binary.sh\",\"command_arguments\":\"$ {infile} $ {job_output_dir}\",\"input_data\":[{\"name\":\"infile\",\"type\":\"file\",\"required\":true,\"media_types\":[\"application/octet-stream\"]}]},\"trigger_rule\":{\"type\":\"PARSE\",\"is_active\":true,\"configuration\":{\"condition\":{\"media_type\":\"application/octet-stream\"},\"data\":{\"input_data_name\":\"infile\",\"workspace_name\":\"products\"},\"version\":\"1.0\"}}}"

COPY parse_binary.sh ./
ENTRYPOINT ["./parse_binary.sh"]

