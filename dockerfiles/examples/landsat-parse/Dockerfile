FROM geoint/landsat-base
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

LABEL com.ngageoint.scale.job-type="{\"name\":\"landsat-parse\",\"version\":\"1.0.0\",\"title\":\"Landsat parse\",\"description\":\"Parse landsat multi-tif files in tar.gz archives\",\"author_name\":\"tclarke@ball.com\",\"docker_image\":\"geoint/parse-landsat\",\"priority\":200,\"timeout\":300,\"max_tries\":3,\"cpus_required\":0.25,\"mem_required\":512,\"interface\":{\"version\":\"1.0\",\"command\":\"./parse_landsat.sh\",\"command_arguments\":\"$ {infile} $ {job_output_dir}\",\"input_data\":[{\"name\":\"infile\",\"type\":\"file\",\"required\":true,\"media_types\":[\"application/octet-stream\"]}],\"output_data\":[{\"name\":\"multispectral\",\"type\":\"file\",\"required\":true,\"media_type\":\"image/tiff\"},{\"name\":\"panchromatic\",\"type\":\"file\",\"required\":true,\"media_type\":\"image/tiff\"},{\"name\":\"thermal\",\"type\":\"file\",\"required\":true,\"media_type\":\"image/tiff\"}]},\"trigger_rule\":{\"type\":\"PARSE\",\"is_active\":true,\"configuration\":{\"condition\":{\"data_types\":[\"landsat\"],\"media_type\":\"application/x-tar\"},\"data\":{\"input_data_name\":\"infile\",\"workspace_name\":\"products\"},\"version\":\"1.0\"}}}"

COPY parse_landsat.sh ./
ENTRYPOINT ["./parse_landsat.sh"]
