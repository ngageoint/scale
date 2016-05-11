FROM iron/java

LABEL com.ngageoint.scale.job-type="{\"name\":\"vash\",\"version\":\"1.0.0\",\"title\":\"Visual hash\",\"description\":\"Generate a Visual Hash (vash) of the data.\",\"author_name\":\"Trevor R.H. Clarke \\u003ctclarke@ball.com\\u003e\",\"docker_image\":\"devdocker-reg.devnet.prv:5000/geoint/vash.0\",\"priority\":250,\"timeout\":300,\"max_tries\":1,\"cpus_required\":0.5,\"mem_required\":100,\"interface\":{\"version\":\"1.0\",\"command\":\"./parse_binary.sh\",\"command_arguments\":\"$ {infile} $ {job_output_dir}\",\"input_data\":[{\"name\":\"infile\",\"type\":\"file\",\"required\":true,\"media_types\":[\"application/octet-stream\"]}],\"output_data\":[{\"name\":\"results\",\"type\":\"file\",\"required\":true,\"media_type\":\"image/jpeg\"}]},\"trigger_rule\":{\"type\":\"PARSE\",\"is_active\":true,\"configuration\":{\"condition\":{\"media_type\":\"application/octet-stream\"},\"data\":{\"input_data_name\":\"infile\",\"workspace_name\":\"products\"},\"version\":\"1.0\"}}}"

WORKDIR /app
ADD . /app

ENTRYPOINT ["./run.sh"]
