FROM geoint/landsat-base
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

LABEL com.ngageoint.scale.job-type="{\"name\":\"landsat-ndwi\",\"version\":\"1.0.0\",\"title\":\"Landsat NDWI\",\"description\":\"Perform NDWI on landsat 8 data.\",\"author_name\":\"tclarke@ball.com\",\"docker_image\":\"geoint/landsat-ndwi\",\"priority\":250,\"timeout\":300,\"max_tries\":3,\"cpus_required\":1,\"mem_required\":1024,\"interface\":{\"version\":\"1.0\",\"command\":\"python landsat_ndwi.py\",\"command_arguments\":\"$ {msi} $ {job_output_dir}\",\"input_data\":[{\"name\":\"msi\",\"type\":\"file\",\"required\":true,\"media_types\":[\"image/tiff\"]}],\"output_data\":[{\"name\":\"ndwi\",\"type\":\"file\",\"required\":true,\"media_type\":\"image/tiff\"}]}}"

COPY landsat_ndwi.py ./
ENTRYPOINT ["/usr/bin/python", "./landsat_ndwi.py"]
