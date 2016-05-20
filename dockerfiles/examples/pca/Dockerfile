FROM tclarke/opticks
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

LABEL com.ngageoint.scale.job-type="{\"name\":\"pca\",\"version\":\"1.0.0\",\"title\":\"Principal Components Analysis\",\"description\":\"Generate Principal Components image.\",\"author_name\":\"Trevor R.H. Clarke \\u003ctclarke@ball.com\\u003e\",\"docker_image\":\"geoint/pca\",\"priority\":250,\"timeout\":300,\"max_tries\":3,\"cpus_required\":2,\"mem_required\":1024,\"interface\":{\"version\":\"1.0\",\"command\":\"./runOpticks.sh\",\"command_arguments\":\"$ {image} $ {job_output_dir}\",\"input_data\":[{\"name\":\"image\",\"type\":\"file\",\"required\":true,\"media_types\":[\"image/tiff\"]}],\"output_data\":[{\"name\":\"pca\",\"type\":\"file\",\"required\":true,\"media_type\":\"image/tiff\"}]}}"

ADD pca.*wiz /wizards/
ADD runOpticks.sh ./
RUN useradd --uid 7498 scale; chown scale /wizards/pca.* runOpticks.sh
USER scale
ENTRYPOINT ["./runOpticks.sh"]
